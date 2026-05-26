from flask import Flask,jsonify, request
from flask_sse import sse
import random
import json
import os
import datetime
import jwt
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import pika
import json
import threading
import sys
import time
from signature import load_or_generate_keys, sign_event, validate_signature
import uuid 

load_dotenv()

app = Flask(__name__)
app.config["REDIS_URL"]="redis://172.17.0.2"

app.register_blueprint(sse, url_prefix='/promotions')

app.config['SECRET_KEY'] = os.getenv("JWT_SECRET")
DB_FILE = 'users.json'

if not os.path.exists(DB_FILE):
    with open(DB_FILE, 'w') as f:
        json.dump({"users": {}}, f)

def load_db():
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token está faltando!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'O token expirou!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token inválido!'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    user_email = data.get('user_email')
    password = data.get('password')
    is_store = data.get('is_store', False)

    if not user_email or not password:
        return jsonify({'message': 'user_email e password são obrigatórios!'}), 400

    db = load_db()
    if user_email in db['users']:
        return jsonify({'message': 'Usuário já existe!'}), 400

    hashed_password = generate_password_hash(password)
    
    db['users'][user_email] = {
        'password': hashed_password,
        'is_store': bool(is_store)
    }
    save_db(db)

    return jsonify({'message': 'Usuário criado com sucesso!'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user_email = data.get('user_email')
    password = data.get('password')

    if not user_email or not password:
        return jsonify({'message': 'Faltando credenciais!'}), 400

    db = load_db()
    user = db['users'].get(user_email)
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'message': 'Credenciais inválidas!'}), 401

    token = jwt.encode({
        'user_email': user_email,
        'is_store': user['is_store'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }, app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({'token': token})

@app.route('/promotion/create', methods=['POST'])
@token_required
def create_promotion(current_user):
    if not current_user.get('is_store'):
        return jsonify({'message': 'Acesso negado! Você não é uma loja.'}), 403

    data = request.get_json()
    promotion_name = data.get('name')
    promotion_value = data.get('value')
    
    if not promotion_name or not promotion_value:
        return jsonify({'message': 'Nome e valor da promoção são obrigatórios!'}), 400



    return jsonify({'message': 'Promoção criada com sucesso!'}), 201

@app.route('/promotion/list', methods=['GET'])
@token_required
def list_promotions(current_user):
    return jsonify({'message': 'Lista de promoções'}), 200

@app.route('/promotion/subscribe', methods=['POST'])
@token_required
def subscribe_promotion(current_user):
    return jsonify({'message': f'Inscrito na categoria com sucesso!'}), 200

@app.route('/promotion/vote', methods=['POST'])
@token_required
def vote_promotion(current_user, promotion_id):
    return jsonify({'message': f'Voto registrado para a promoção {promotion_id}'}), 200

@app.route('/notifications/unsubscribe', methods=['POST'])
@token_required
def cancel_subscribe(current_user):
    return jsonify({'message': f'Inscrição cancelada com sucesso!'}), 200


INSTANCE_ID = str(uuid.uuid4())[:8]
client_queue_name = f"queue_client_{INSTANCE_ID}"

EXCHANGE_NAME = 'Promocoes'

private_key, public_key = load_or_generate_keys("gateway")
_, promo_pub_key = load_or_generate_keys("promocao")

validated_promotions = []

def get_new_connection():
    """Cria uma nova conexão limpa para evitar conflitos entre threads"""
    params = pika.ConnectionParameters(host='localhost', heartbeat=600)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic')
    return connection, channel

def publish_event(routing_key, data):
    try:
        conn, ch = get_new_connection()
        signature = sign_event(private_key, data)
        message = {"dados": data, "Signature": signature}
        ch.basic_publish(exchange=EXCHANGE_NAME, routing_key=routing_key, body=json.dumps(message))
        conn.close() 
    except Exception as e:
        print(f"\n[Erro de Publicação] {e}")

def consume_validation_events():
    try:
        conn, ch = get_new_connection()
        result = ch.queue_declare(queue='', durable=False, exclusive=True)
        q_name = result.method.queue
        ch.queue_bind(exchange=EXCHANGE_NAME, queue=q_name, routing_key='promocao.publicada')

        def callback(ch, method, properties, body):
            message = json.loads(body)
            if validate_signature(promo_pub_key, message['dados'], message['Signature']):
                data = message['dados']
                if not any(p['id'] == data['id'] for p in validated_promotions):
                    validated_promotions.append(data)
                    save_promotions()

        ch.basic_consume(queue=q_name, on_message_callback=callback, auto_ack=True)
        ch.start_consuming()
    except Exception as e:
        print(f"\n[Erro na Thread de Validação] {e}")

def consume_client_notifications():
    """Thread dedicada apenas para as notificações do usuário"""
    global client_queue_name
    try:
        conn, ch = get_new_connection()
        
        ch.queue_declare(queue=client_queue_name, durable=False, exclusive=False, auto_delete=True)
        ch.queue_bind(exchange=EXCHANGE_NAME, queue=client_queue_name, routing_key='promocao.destaque_notificacao')

        def callback(ch, method, properties, body):
            data = json.loads(body)
            print(f"\n\n🔔 [NOTIFICAÇÃO - Tópico: {method.routing_key}] 🔔")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("\nPressione ENTER para continuar...", end="", flush=True)

        ch.basic_consume(queue=client_queue_name, on_message_callback=callback, auto_ack=True)
        ch.start_consuming()
    except Exception as e:
        print(f"\n[Erro na Thread de Notificações] {e}")

def subscribe_to_category(category):
    """Faz o binding usando uma conexão temporária na fila da instância"""
    if not client_queue_name:
        print("\n[!] Fila de notificações não está pronta.")
        return
    try:
        conn, ch = get_new_connection()
        routing_key = f"promocao.{category.lower()}"
        ch.queue_bind(exchange=EXCHANGE_NAME, queue=client_queue_name, routing_key=routing_key)
        print(f"\n[Sucesso] Inscrito na categoria: {category}")
        conn.close()
    except Exception as e:
        print(f"\n[Erro na Inscrição] {e}")