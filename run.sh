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

echo "💻 Subindo o Frontend Web (React)..."
# Entra na pasta do frontend e inicia a aplicação React
gnome-terminal --title="Frontend React" -- bash -c "cd frontend-promocoes && npm start; exec bash"

echo "✅ Todos os serviços disparados no ambiente '$ENV_NAME'."