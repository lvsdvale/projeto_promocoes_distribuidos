# gateway.py
from flask import Flask, jsonify, request
from flask_sse import sse
import json
import os
import datetime
import jwt
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import pika
import threading
from signature import load_or_generate_keys, sign_event, validate_signature
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config["REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379")
app.register_blueprint(sse, url_prefix='/promotions/stream')

app.config['SECRET_KEY'] = 'utfpr_sistemas_distribuidos_secret'
USER_DB = 'users.json'

private_key, public_key = load_or_generate_keys("gateway")
_, promo_pub_key = load_or_generate_keys("promocao")
_, notif_pub_key = load_or_generate_keys("notificacao")

if not os.path.exists(USER_DB):
    with open(USER_DB, 'w') as f:
        json.dump({"users": {}}, f)

def load_users():
    with open(USER_DB, 'r') as f: return json.load(f)

def save_users(data):
    with open(USER_DB, 'w') as f: json.dump(data, f, indent=4)

cached_promotions = []

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            parts = request.headers['Authorization'].split(" ")
            if len(parts) == 2: token = parts[1]
        
        if not token:
            return jsonify({'message': 'Token de autenticação ausente!'}), 401
        try:
            current_user = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except:
            return jsonify({'message': 'Token inválido ou expirado!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('user_email')
    password = data.get('password')
    is_store = data.get('is_store', False) # True se for loja, False se for cliente normal

    if not email or not password:
        return jsonify({'message': 'Preencha todos os campos obrigatórios!'}), 400

    db = load_users()
    if email in db['users']:
        return jsonify({'message': 'Este e-mail já está cadastrado!'}), 400

    db['users'][email] = {
        'password': generate_password_hash(password),
        'is_store': bool(is_store),
        'interests': []
    }
    save_users(db)
    return jsonify({'message': 'Usuário registrado com sucesso!'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('user_email')
    password = data.get('password')

    db = load_users()
    user = db['users'].get(email)
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'message': 'Credenciais incorretas!'}, 401)

    token = jwt.encode({
        'user_email': email,
        'is_store': user['is_store'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }, app.config['SECRET_KEY'], algorithm='HS256')
    
    return jsonify({'token': token, 'is_store': user['is_store']})

@app.route('/promotion/create', methods=['POST'])
@token_required
def create_promotion(current_user):
    if not current_user.get('is_store'):
        return jsonify({'message': 'Acesso negado!'}), 403

    body = request.get_json()
    email_loja = current_user.get('user_email')
    body['email_loja'] = email_loja
    private_key_loja, _ = load_or_generate_keys("loja")
    signature = sign_event(private_key_loja, body)

    payload_completo = {
        "dados": body,
        "Signature": signature
    }
    print(f"Enviando promoção com payload: {payload_completo}")
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.basic_publish(exchange='Promocoes', routing_key='promocao.recebida', body=json.dumps(payload_completo))
    connection.close()

    return jsonify({'message': 'Promoção enviada com sucesso!'}), 202
@app.route('/promotion/list', methods=['GET'])
@token_required
def list_promotions(current_user):
    return jsonify({'promotions': cached_promotions}), 200

@app.route('/promotion/vote', methods=['POST'])
@token_required
def vote_promotion(current_user):
    if current_user.get('is_store'):
        return jsonify({'message': 'Acesso negado. Lojas não podem votar em promoções!'}), 403

    data = request.get_json()
    promo_id = data.get('promotion_id')
    vote_value = data.get('vote')

    if not promo_id or vote_value not in [1, -1]:
        return jsonify({'message': 'Dados de votação inválidos!'}), 400

    payload_voto = {'promotion_id': promo_id, 'vote': vote_value, 'user': current_user['user_email']}
    signature = sign_event(private_key, payload_voto)
    message = {"dados": payload_voto, "Signature": signature}

    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.basic_publish(exchange='Promocoes', routing_key='promocao.voto', body=json.dumps(message))
    connection.close()

    return jsonify({'message': 'Voto encaminhado com sucesso!'}), 202

@app.route('/promotion/subscribe', methods=['POST'])
@token_required
def subscribe_category(current_user):
    if current_user.get('is_store'):
        return jsonify({'message': 'Lojas não gerenciam tópicos de interesse!'}), 403

    category = request.get_json().get('category', '').lower()
    if not category: return jsonify({'message': 'Categoria inválida!'}), 400

    db = load_users()
    if category not in db['users'][current_user['user_email']]['interests']:
        db['users'][current_user['user_email']]['interests'].append(category)
        save_users(db)
    return jsonify({'message': f'Inscrito na categoria: {category}'}), 200

@app.route('/notifications/unsubscribe', methods=['POST'])
@token_required
def unsubscribe_category(current_user):
    category = request.get_json().get('category', '').lower()
    db = load_users()
    if category in db['users'][current_user['user_email']]['interests']:
        db['users'][current_user['user_email']]['interests'].remove(category)
        save_users(db)
    return jsonify({'message': f'Inscrição removida de: {category}'}), 200

def background_mom_listener():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.exchange_declare(exchange='Promocoes', exchange_type='topic')
    
    result = channel.queue_declare(queue='', exclusive=True)
    q_name = result.method.queue

    channel.queue_bind(exchange='Promocoes', queue=q_name, routing_key='promocao.publicada')
    channel.queue_bind(exchange='Promocoes', queue=q_name, routing_key='promocao.categoria')
    channel.queue_bind(exchange='Promocoes', queue=q_name, routing_key='notificação.hotdeal')

    def callback(ch, method, properties, body):
        global cached_promotions
        message = json.loads(body)
        data = message.get('dados')
        sig = message.get('Signature')
        rk = method.routing_key

        if rk == 'promocao.publicada':
            if validate_signature(promo_pub_key, data, sig):
                if not any(p.get('id') == data.get('id') for p in cached_promotions):
                    cached_promotions.append(data)
                    with app.app_context():
                        sse.publish(data, type='nova_promocao_geral')

        elif rk == 'promocao.categoria':
            if validate_signature(notif_pub_key, data, sig):
                target_cat = data.get('categoria', '').lower()
                db = load_users()
                with app.app_context():
                    for email, profile in db['users'].items():
                        if target_cat in profile.get('interests', []):
                            sse.publish(data, type='categoria_update', channel=email)

        elif rk == 'notificação.hotdeal':
            if validate_signature(notif_pub_key, data, sig):
                with app.app_context():
                    sse.publish(data, type='hotdeal_broadcast')

    channel.basic_consume(queue=q_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

threading.Thread(target=background_mom_listener, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)