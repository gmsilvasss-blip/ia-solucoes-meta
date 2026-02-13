import os
import requests  # Importante: adicione 'requests' no seu requirements.txt
from flask import Flask, request, jsonify, render_template

app = Flask(__name__, template_folder='.')

# Puxando as variáveis que você acabou de salvar no Render
APP_ID = os.environ.get('App_Id')
VERIFY_TOKEN = os.environ.get('Verify_Token_Webhook')
WA_TOKEN = os.environ.get('WHATSAPP_TOKEN')
PHONE_ID = os.environ.get('PHONE_NUMBER_ID')

@app.route('/')
def home():
    return render_template('index.html', app_id=APP_ID)

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        return "Erro", 403
                
    elif request.method == 'POST':
        data = request.json
        
        # Lógica para detectar mensagem de texto e responder
        if data.get('entry') and data['entry'][0].get('changes'):
            change = data['entry'][0]['changes'][0]['value']
            if change.get('messages'):
                msg = change['messages'][0]
                numero_remetente = msg['from']
                texto_recebido = msg.get('text', {}).get('body', '')

                # Chama a função para responder
                enviar_resposta(numero_remetente, f"Oráculo recebeu: {texto_recebido}")

        return jsonify({"status": "ok"}), 200

def enviar_resposta(para, texto):
    url = f"https://graph.facebook.com/v21.0/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WA_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": para,
        "type": "text",
        "text": {"body": texto}
    }
    requests.post(url, json=payload, headers=headers)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
