import pika
import json
import os
from signature import load_or_generate_keys, sign_event, validate_signature

EXCHANGE_NAME = 'Promocoes'
DB_FILE = 'promocoes_db.json'

private_key, public_key = load_or_generate_keys("promocao")
_, loja_pub_key = load_or_generate_keys("loja")

if not os.path.exists(DB_FILE):
    with open(DB_FILE, 'w') as f: json.dump([], f)

def salvar_promocao(dados):
    with open(DB_FILE, 'r+') as f:
        promos = json.load(f)
        promos.append(dados)
        f.seek(0)
        json.dump(promos, f, indent=4)

def process_promotion(ch, method, properties, body):
    message = json.loads(body)
    data = message['dados']
    signature = message['Signature']

    print(f"[MS Promoção] Validando promoção: {data.get('nome')}")
    
    if validate_signature(loja_pub_key, data, signature):
        print("[MS Promoção] Assinatura da Loja confirmada. Salvando...")
        salvar_promocao(data)
        
        new_signature = sign_event(private_key, data)
        new_message = {"dados": data, "Signature": new_signature}
        
        ch.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key='promocao.publicada',
            body=json.dumps(new_message)
        )
    else:
        print("[MS Promoção] Assinatura inválida detectada! Descartando evento.")

if __name__ == '__main__':
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic')
    
    result = channel.queue_declare(queue='fila_validacao_promocao', durable=True)
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=result.method.queue, routing_key='promocao.recebida')
    
    print(" [*] MS Promoção aguardando mensagens no Broker...")
    channel.basic_consume(queue=result.method.queue, on_message_callback=process_promotion, auto_ack=True)
    channel.start_consuming()