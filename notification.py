import pika
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from signature import load_or_generate_keys, sign_event, validate_signature
from dotenv import load_dotenv
import os

load_dotenv()

def enviar_email_hotdeal(email_loja, nome_produto, id_produto):
    REMETENTE = os.getenv("EMAIL_REMETENTE")
    SENHA_APP = os.getenv("EMAIL_SENHA_APP")
    
    msg = MIMEMultipart()
    msg['From'] = REMETENTE
    msg['To'] = email_loja
    msg['Subject'] = f"🔥 PARABÉNS! Seu produto {nome_produto} é um Hot Deal!"
    
    corpo = f"""
    Olá, Parceiro!
    
    Temos uma ótima notícia: A sua promoção do produto "{nome_produto}" (ID: {id_produto}) 
    acabou de atingir o limite de votos positivos na nossa plataforma e se tornou um HOT DEAL!
    
    Prepare seu estoque, pois a visibilidade dele acabou de aumentar muito!
    
    Atenciosamente,
    Equipe do Sistema de Promoções
    """
    msg.attach(MIMEText(corpo, 'plain', 'utf-8'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(REMETENTE, SENHA_APP)
        server.send_message(msg)
        server.quit()
        print(f"[MS Notificação] 📧 E-mail de Hot Deal enviado com sucesso para {email_loja}!")
    except Exception as e:
        print(f"[MS Notificação] ❌ Erro ao enviar o e-mail: {e}")

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
            
            nome_prod = data.get('nome', 'Produto em Destaque')
            id_prod = data.get('id', 'N/A')
            
            email_destino = data.get('email_loja', 'seu_email_pessoal_para_teste@gmail.com')
            

            enviar_email_hotdeal(email_destino, nome_prod, id_prod)

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