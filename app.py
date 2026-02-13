import os
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Puxa o APP_ID da variável de ambiente do Render
# Se não encontrar, ele fica vazio (mas o ideal é estar configurado lá)
APP_ID = os.environ.get('APP_ID')

# Puxa o Token de Verificação da variável de ambiente ou usa o padrão
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN', 'meu_token_secreto_do_oraculo')

@app.route('/')
def home():
    # Passamos o APP_ID que veio do ambiente para o index.html
    return render_template('index.html', app_id=APP_ID)

@app.route('/exclusao')
def exclusao():
    return render_template('exclusao.html')

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode and token:
            if mode == 'subscribe' and token == VERIFY_TOKEN:
                print("WEBHOOK_VERIFICADO")
                return challenge, 200
            else:
                return "Token de verificação inválido", 403
                
    elif request.method == 'POST':
        data = request.json
        # Imprime no log do Render para podermos debugar
        print("Mensagem recebida:", data)
        return jsonify({"status": "sucesso"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
