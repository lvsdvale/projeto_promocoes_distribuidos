#!/bin/bash

# Nome do seu ambiente conda
ENV_NAME="redes"

echo "🚀 Iniciando ecossistema no ambiente Conda: $ENV_NAME"

# (Opcional) Tenta garantir que o redis e o rabbitmq estão rodando
# sudo systemctl start redis rabbitmq-server

# Função para abrir o terminal já rodando o comando dentro do ambiente conda
# Usamos 'conda run -n nome_do_env' para garantir o contexto correto

echo "⚙️ Subindo os Workers do RabbitMQ..."
gnome-terminal --title="MS Promoção" -- bash -c "conda run -n $ENV_NAME --no-capture-output python3 promo.py; exec bash"
gnome-terminal --title="MS Ranking" -- bash -c "conda run -n $ENV_NAME --no-capture-output python3 ranking.py; exec bash"
gnome-terminal --title="MS Notificação" -- bash -c "conda run -n $ENV_NAME --no-capture-output python3 notification.py; exec bash"

echo "⏳ Aguardando os microsserviços se conectarem ao Broker..."
sleep 2

echo "⚙️ Subindo o API Gateway (REST + SSE)..."
gnome-terminal --title="MS Gateway" -- bash -c "conda run -n $ENV_NAME --no-capture-output python3 gateway.py; exec bash"

echo "⏳ Aguardando o Gateway iniciar na porta 5000..."
sleep 3

# Descomente a linha abaixo se for testar com aquele script frontend_client.py que criei
# gnome-terminal --title="Cliente Frontend" -- bash -c "conda run -n $ENV_NAME --no-capture-output python3 frontend_client.py; exec bash"

# Descomente a linha abaixo se quiser já abrir um terminal para a Loja simular envio de promoções
# gnome-terminal --title="Loja Publisher" -- bash -c "conda run -n $ENV_NAME --no-capture-output python3 store_publisher.py; exec bash"

echo "✅ Todos os serviços disparados no ambiente '$ENV_NAME'."