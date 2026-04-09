import pika
import json
from signature import load_or_generate_keys, sign_event, validate_signature

EXCHANGE_NAME = 'Promocoes'
_, promo_pub_key = load_or_generate_keys("promocao")
_, ranking_pub_key = load_or_generate_keys("ranking")

def process_notification(ch, method, properties, body):
    message = json.loads(body)
    data = message['dados']
    signature = message['Signature']
    routing_key = method.routing_key

    if routing_key == 'promocao.publicada':
        if validate_signature(promo_pub_key, data, signature):
            category = data.get('categoria', 'geral')
            new_rk = f"promocao.{category}"
            print(f"[MS Notificação] Direcionando {data['nome']} para {new_rk}")
            ch.basic_publish(exchange=EXCHANGE_NAME, routing_key=new_rk, body=json.dumps(data))
            
    elif routing_key == 'promocao.destaque':
        if validate_signature(ranking_pub_key, data, signature):
            print(f"[MS Notificação] Anunciando HOT DEAL para ID {data['id']}")
            data['alerta'] = '🔥 HOT DEAL 🔥'
            ch.basic_publish(exchange=EXCHANGE_NAME, routing_key='promocao.destaque_notificacao', body=json.dumps(data))

if __name__ == '__main__':
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic')
    
    result = channel.queue_declare(queue='', exclusive=True)
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=result.method.queue, routing_key='promocao.publicada')
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=result.method.queue, routing_key='promocao.destaque')
    
    print(" [*] MS Notificação operacional...")
    channel.basic_consume(queue=result.method.queue, on_message_callback=process_notification, auto_ack=True)
    channel.start_consuming()