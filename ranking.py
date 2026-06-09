# ranking.py
import pika
import json
from signature import load_or_generate_keys, sign_event, validate_signature

EXCHANGE_NAME = 'Promocoes'
HOT_DEAL_LIMIT = 5

private_key, public_key = load_or_generate_keys("ranking")
_, gateway_pub_key = load_or_generate_keys("gateway")

vote_ranking = {}
promocoes_cache = {} # 🌟 FALTAVA ISSO: Cache para associar o ID ao Nome e E-mail da loja

def process_vote(ch, method, properties, body):
    message = json.loads(body)
    data = message['dados']
    signature = message['Signature']
    routing_key = method.routing_key

    if routing_key == 'promocao.publicada':
        id_promo = data.get('id')
        if id_promo:
            promocoes_cache[id_promo] = {
                "nome": data.get('nome'),
                "email_loja": data.get('email_loja') 
            }
            print(f"[MS Ranking] 📥 Cache atualizado: ID {id_promo} pertence a {data.get('email_loja')}")
        return

    if routing_key == 'promocao.voto':
        if validate_signature(gateway_pub_key, data, signature):
            id_promo = data['promotion_id']
            vote = data['vote']
            
            vote_ranking[id_promo] = vote_ranking.get(id_promo, 0) + vote
            print(f"[MS Ranking] Promoção ID {id_promo} | Score Atual: {vote_ranking[id_promo]}")
            
            if vote_ranking[id_promo] >= HOT_DEAL_LIMIT:
                print(f"🔥 [MS Ranking] Promoção {id_promo} virou destaque!")
                
                dados_loja = promocoes_cache.get(id_promo, {})
                nome_prod = dados_loja.get('nome', 'Produto Especial')
                email_loja = dados_loja.get('email_loja', 'seu_email_pessoal_para_teste@gmail.com')
                
                highlight_data = {
                    "id": id_promo, 
                    "nome": nome_prod,       
                    "email_loja": email_loja,    
                    "status": "hot deal", 
                    "score": vote_ranking[id_promo]
                }
                
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
    
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=result.method.queue, routing_key='promocao.publicada')
    
    print(" [*] MS Ranking aguardando computação de votos e dados de promoções...")
    channel.basic_consume(queue=result.method.queue, on_message_callback=process_vote, auto_ack=True)
    channel.start_consuming()