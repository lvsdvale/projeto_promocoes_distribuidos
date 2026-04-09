import pika
import json
import threading
import sys
import time
from signature import load_or_generate_keys, sign_event, validate_signature
import uuid 

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
    """Abre uma conexão temporária, publica e fecha imediatamente"""
    try:
        conn, ch = get_new_connection()
        signature = sign_event(private_key, data)
        message = {"dados": data, "Signature": signature}
        ch.basic_publish(exchange=EXCHANGE_NAME, routing_key=routing_key, body=json.dumps(message))
        conn.close() 
    except Exception as e:
        print(f"\n[Erro de Publicação] {e}")

def consume_validation_events():
    """Thread dedicada apenas para atualizar a lista de promoções"""
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


def display_store_panel():
    while True:
        print("\n" + "="*30 + "\n🏢 PAINEL DA LOJA\n" + "="*30)
        print("1. Cadastrar Nova Promoção\n0. Voltar")
        choice = input("\nSeleção: ")
        if choice == '1':
            name = input("Nome do Produto: ")
            cat = input("Categoria: ")
            promo_id = int(time.time())
            publish_event('promocao.recebida', {"id": promo_id, "nome": name, "categoria": cat.lower()})
            print(f"\n[✓] '{name}' enviada para validação!")
        elif choice == '0': break

def display_client_panel():
    threading.Thread(target=consume_client_notifications, daemon=True).start()
    while True:
        print("\n" + "="*30 + "\n👤 PAINEL DO CLIENTE\n" + "="*30)
        print("1. Listar Promoções Ativas")
        print("2. Votar em uma Promoção")
        print("3. Assinar uma Categoria")
        print("0. Voltar")
        choice = input("\nSeleção: ")
        if choice == '1':
            print("\n--- Promoções Ativas ---")
            if not validated_promotions:
                print("Nenhuma promoção disponível no momento.")
            for p in validated_promotions:
                print(f"ID: {p['id']} | {p['nome']} [{p['categoria']}]")
            input("\nPressione ENTER para continuar...")
        elif choice == '2':
            try:
                pid = int(input("ID da Promoção: "))
                v = int(input("Voto (1: Gostei, -1: Não Gostei): "))
                if v not in [1, -1]:
                    print("Voto inválido! Use 1 ou -1.")
                    continue
                publish_event('promocao.voto', {"id": pid, "voto": v})
                print("[✓] Voto enviado!")
            except: print("Entrada inválida. Digite apenas números.")
        elif choice == '3':
            cat = input("Categoria para seguir: ")
            subscribe_to_category(cat.strip())
        elif choice == '0': break

def display_main_menu():
    while True:
        print("\n" + "#"*40 + "\n  GATEWAY DE PROMOÇÕES DISTRIBUÍDAS\n" + "#"*40)
        print("[ 1 ] Acessar como LOJA\n[ 2 ] Acessar como CLIENTE\n[ 0 ] Sair")
        choice = input("\nPerfil: ")
        if choice == '1': display_store_panel()
        elif choice == '2': display_client_panel()
        elif choice == '0': sys.exit(0)

if __name__ == '__main__':
    threading.Thread(target=consume_validation_events, daemon=True).start()
    display_main_menu()