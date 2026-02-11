import os
from flask import Flask, request, render_template
from dotenv import load_dotenv

load_dotenv('env.env')

# O template_folder='.' diz para o Flask buscar o index.html na raiz do projeto
app = Flask(__name__, template_folder='.')

APP_ID = os.getenv('App_Id')
BUSINESS_ID = os.getenv('Business_Id') or os.getenv('BUSINESS_ID')
VERIFY_TOKEN = os.getenv('Verify_Token_Webhook')

@app.route('/')
def home():
    # Passa o APP_ID para o HTML poder carregar o botão da Meta
    return render_template('index.html', app_id=APP_ID)

@app.route('/exclusao')
def exclusao():
    return render_template('exclusao.html')

@app.route('/webhook', methods=['GET'])
def verify():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Token de verificação inválido", 403
    return "Faltam parâmetros", 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)