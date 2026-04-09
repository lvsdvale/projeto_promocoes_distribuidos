#!/bin/bash

# Nome do seu ambiente conda
ENV_NAME="redes"

echo "🚀 Iniciando ecossistema no ambiente Conda: $ENV_NAME"

# Função para abrir o terminal já rodando o comando dentro do ambiente conda
# Usamos 'conda run -n nome_do_env' para garantir o contexto correto
gnome-terminal --title="MS Promoção" -- bash -c "conda run -n $ENV_NAME --no-capture-output python3 promo.py; exec bash"
gnome-terminal --title="MS Ranking" -- bash -c "conda run -n $ENV_NAME --no-capture-output python3 ranking.py; exec bash"
gnome-terminal --title="MS Notificação" -- bash -c "conda run -n $ENV_NAME --no-capture-output python3 notification.py; exec bash"

echo "⏳ Aguardando backends..."
sleep 2

# Gateways para Loja e Cliente
gnome-terminal --title="Gateway - Loja" -- bash -c "conda run -n $ENV_NAME --no-capture-output python3 gateway.py; exec bash"
gnome-terminal --title="Gateway - Cliente" -- bash -c "conda run -n $ENV_NAME --no-capture-output python3 gateway.py; exec bash"

echo "✅ Todos os serviços disparados no ambiente '$ENV_NAME'."