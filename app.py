import os
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

# Carrega as variáveis do seu arquivo específico env.env
# O Render também permite configurar estas variáveis diretamente no painel deles
load_dotenv('env.env')

# 'template_folder="."' diz ao Flask para procurar o index.html na mesma pasta do app.py
app = Flask(__name__)

# Puxando as variáveis do seu arquivo .env
VERIFY_TOKEN = os.getenv('Verify_Token_Webhook')
APP_ID = os.getenv('App_ID')

@app.route('/')
def home():
    # Isso vai renderizar o seu arquivo index.html no link principal
    return render_template('index.html', app_id=APP_ID)

# ROTA DE WEBHOOK (Verificação e Recebimento)
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print("WEBHOOK_VERIFICADO COM SUCESSO!")
            return challenge, 200
        else:
            return "Token de verificação inválido", 403

    if request.method == 'POST':
        data = request.json
        # Aqui você receberá os tokens do Embedded Signup ou mensagens de clientes
        print("Dados recebidos da Meta:", data)
        return "EVENT_RECEIVED", 200

if __name__ == '__main__':
    # O Render define a porta automaticamente na variável de ambiente PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)