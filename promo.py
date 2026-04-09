import pika
import json
from signature import load_or_generate_keys, sign_event, validate_signature

EXCHANGE_NAME = 'Promocoes'
private_key, public_key = load_or_generate_keys("promocao")
_, gateway_pub_key = load_or_generate_keys("gateway")

def process_promotion(ch, method, properties, body):
    message = json.loads(body)
    data = message['dados']
    signature = message['Signature']

    print(f"[MS Promoção] Analisando promoção recebida: {data['nome']}")
    
    if validate_signature(gateway_pub_key, data, signature):
        print("[MS Promoção] Assinatura do Gateway válida. Aprovando promoção...")
        
        new_signature = sign_event(private_key, data)
        new_message = {"dados": data, "Signature": new_signature}
        
        ch.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key='promocao.publicada',
            body=json.dumps(new_message)
        )
    else:
        print("[MS Promoção] Assinatura inválida! Evento descartado.")

if __name__ == '__main__':
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic')
    
    result = channel.queue_declare(queue='', exclusive=True)
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=result.method.queue, routing_key='promocao.recebida')
    
    print(" [*] MS Promoção aguardando eventos. Para sair pressione CTRL+C")
    channel.basic_consume(queue=result.method.queue, on_message_callback=process_promotion, auto_ack=True)
    channel.start_consuming()