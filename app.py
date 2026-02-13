import os
from flask import Flask, request, jsonify, render_template

# Configuramos o template_folder como '.' para indicar que os HTMLs estão na raiz
app = Flask(__name__, template_folder='.')

APP_ID = os.environ.get('App_Id', '1167445461916695')
VERIFY_TOKEN = os.environ.get('Verify_Token_Webhook', 'webhookkey')

@app.route('/')
def home():
    # Agora ele vai procurar o index.html na mesma pasta do app.py
    return render_template('index.html', app_id=APP_ID)

@app.route('/exclusao')
def exclusao():
    # O mesmo para o exclusao.html
    return render_template('exclusao.html')

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        return "Token de verificação inválido", 403
                
    elif request.method == 'POST':
        data = request.json
        print("Webhook recebido:", data)
        return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
