import pika
import json

EXCHANGE_NAME = 'Promocoes'

def start_client(interest_categories):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic')

    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    for category in interest_categories:
        routing_key = f"promocao.{category}"
        channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name, routing_key=routing_key)
        print(f"[*] Inscrito na categoria: {category}")
    
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name, routing_key='promocao.destaque_notificacao')
    print("[*] Inscrito em HOT DEALS!")

    def callback(ch, method, properties, body):
        data = json.loads(body)
        print(f"\n[NOVA NOTIFICAÇÃO - {method.routing_key}]")
        for k, v in data.items():
            print(f"  {k.capitalize()}: {v}")
        print("-" * 30)

    print("\nAguardando notificações...")
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == '__main__':
    my_categories = ['livro', 'jogo'] 
    start_client(my_categories)