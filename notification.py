
import pika
import json
from signature import load_or_generate_keys, sign_event, validate_signature

EXCHANGE_NAME = 'Promocoes'
private_key, public_key = load_or_generate_keys("notificacao")
_, promo_pub_key = load_or_generate_keys("promocao")
_, ranking_pub_key = load_or_generate_keys("ranking")

def process_notification(ch, method, properties, body):
    message = json.loads(body)
    data = message['dados']
    signature = message['Signature']
    routing_key = method.routing_key

    if routing_key == 'promocao.publicada':
        if validate_signature(promo_pub_key, data, signature):
            new_sig = sign_event(private_key, data)
            ch.basic_publish(
                exchange=EXCHANGE_NAME,
                routing_key='promocao.categoria',
                body=json.dumps({"dados": data, "Signature": new_sig})
            )
            print(f"[MS Notificação] Promoção roteada para a categoria: {data.get('categoria')}")
            
    elif routing_key == 'promocao.destaque':
        if validate_signature(ranking_pub_key, data, signature):
            print(f"[MS Notificação] Processando Alerta de Hot Deal global.")
            data['alerta'] = '🔥 HOT DEAL 🔥'
            new_sig = sign_event(private_key, data)
            ch.basic_publish(
                exchange=EXCHANGE_NAME,
                routing_key='notificação.hotdeal',
                body=json.dumps({"dados": data, "Signature": new_sig})
            )

if __name__ == '__main__':
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic')
    
    result = channel.queue_declare(queue='fila_notificacoes', durable=True)
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=result.method.queue, routing_key='promocao.publicada')
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=result.method.queue, routing_key='promocao.destaque')
    
    print(" [*] MS Notificação ativo no barramento...")
    channel.basic_consume(queue=result.method.queue, on_message_callback=process_notification, auto_ack=True)
    channel.start_consuming()