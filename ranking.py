# ranking.py
import pika
import json
from signature import load_or_generate_keys, sign_event, validate_signature

EXCHANGE_NAME = 'Promocoes'
HOT_DEAL_LIMIT = 5

private_key, public_key = load_or_generate_keys("ranking")
_, gateway_pub_key = load_or_generate_keys("gateway")

vote_ranking = {}

def process_vote(ch, method, properties, body):
    message = json.loads(body)
    data = message['dados']
    signature = message['Signature']

    if validate_signature(gateway_pub_key, data, signature):
        id_promo = data['promotion_id']
        vote = data['vote']
        
        vote_ranking[id_promo] = vote_ranking.get(id_promo, 0) + vote
        print(f"[MS Ranking] Promoção ID {id_promo} | Score Atual: {vote_ranking[id_promo]}")
        
        if vote_ranking[id_promo] >= HOT_DEAL_LIMIT:
            print(f"🔥 [MS Ranking] Promoção {id_promo} virou destaque!")
            highlight_data = {"id": id_promo, "status": "hot deal", "score": vote_ranking[id_promo]}
            
            new_signature = sign_event(private_key, highlight_data)
            new_message = {"dados": highlight_data, "Signature": new_signature}
            
            ch.basic_publish(
                exchange=EXCHANGE_NAME,
                routing_key='promocao.destaque',
                body=json.dumps(new_message)
            )
    else:
        print("[MS Ranking] Assinatura do voto inválida! Ignorando processamento.")

if __name__ == '__main__':
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic')
    
    result = channel.queue_declare(queue='fila_ranking_votos', durable=True)
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=result.method.queue, routing_key='promocao.voto')
    
    print(" [*] MS Ranking aguardando computação de votos...")
    channel.basic_consume(queue=result.method.queue, on_message_callback=process_vote, auto_ack=True)
    channel.start_consuming()