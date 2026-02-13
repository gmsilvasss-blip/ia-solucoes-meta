import os
from flask import Flask, request, jsonify, render_template

app = Flask(__name__, template_folder='.')

# Puxando as chaves com um "fallback" para não dar erro 500
# Ele tenta pegar do Render, se não tiver, usa o que está entre aspas
APP_ID = os.environ.get('App_Id')
VERIFY_TOKEN = os.environ.get('Verify_Token_Webhook')

@app.route('/')
def home():
    try:
        return render_template('index.html', app_id=APP_ID)
    except Exception as e:
        return f"Erro ao carregar template: {str(e)}", 500

@app.route('/exclusao')
def exclusao():
    return render_template('exclusao.html')

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        return "Token Inválido", 403
                
    elif request.method == 'POST':
        # Retornamos 200 rápido para a Meta não achar que estamos fora do ar
        return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


