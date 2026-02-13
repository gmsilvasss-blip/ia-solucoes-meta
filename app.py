import os
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Puxando as chaves oficiais do seu painel conforme a imagem image_9714b7.png
APP_ID = os.environ.get('App_Id')
VERIFY_TOKEN = os.environ.get('Verify_Token_Webhook')

@app.route('/')
def home():
    # Renderiza o index enviando o APP_ID para o JavaScript do Embedded
    return render_template('index.html', app_id=APP_ID)

@app.route('/exclusao')
def exclusao():
    return render_template('exclusao.html')

# ROTA DO WEBHOOK - É aqui que a Meta vai enviar as dúvidas da turma
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # Validação (GET)
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print("WEBHOOK VERIFICADO COM SUCESSO!")
            return challenge, 200
        else:
            return "Token de verificação inválido", 403
                
    # Recebimento de Mensagens (POST)
    elif request.method == 'POST':
        data = request.json
        # Esse print aparecerá nos logs do Render quando um aluno mandar mensagem
        print("Nova mensagem do aluno detectada:", data)
        
        # Resposta 200 para a Meta não achar que o servidor caiu
        return jsonify({"status": "recebido"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
