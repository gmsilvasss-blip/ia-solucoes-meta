import os
import logging
import requests
from flask import Flask, request, jsonify, render_template

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='.')

# --- VARIÁVEIS DE AMBIENTE (Puxadas do Render) ---
APP_ID = os.environ.get('App_Id')
APP_SECRET = os.environ.get('App_Secret')
WA_TOKEN = os.environ.get('WHATSAPP_TOKEN')
PHONE_ID = os.environ.get('PHONE_NUMBER_ID')
VERIFY_TOKEN = os.environ.get('Verify_Token_Webhook', 'webhookkey')

# Configuração da IA (Ajuste conforme sua chave da OpenAI/Anthropic/Gemini)
AI_API_KEY = os.environ.get('AI_API_KEY')

@app.route('/')
def home():
    """Página inicial com o botão de Login da Meta"""
    return render_template('index.html', app_id=APP_ID)

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # Validação do Webhook (GET)
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode == 'subscribe' and token == VERIFY_TOKEN:
            logger.info("WEBHOOK_VERIFIED")
            return challenge, 200
        else:
            return 'Verification token mismatch', 403

    # Recebimento de Mensagens (POST)
    if request.method == 'POST':
        data = request.json
        
        # Log para debug (aparecerá no Render)
        logger.info(f"Dados recebidos do WhatsApp: {data}")

        if is_valid_message(data):
            msg_body = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
            from_number = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
            
            # 1. Chamar a função do Oráculo (RAG + IA)
            resposta_ia = processar_oraculo(msg_body)
            
            # 2. Enviar resposta de volta para o usuário
            enviar_mensagem_whatsapp(from_number, resposta_ia)

        return jsonify({"status": "ok"}), 200

def is_valid_message(data):
    """Verifica se o JSON recebido contém uma mensagem de texto válida"""
    try:
        return 'messages' in data['entry'][0]['changes'][0]['value']
    except:
        return False

def processar_oraculo(pergunta):
    """
    Aqui fica a lógica do RAG:
    1. Busca no Banco Vetorial
    2. Envia contexto + pergunta para a IA
    """
    logger.info(f"Processando pergunta: {pergunta}")
    # Por enquanto retorna um eco, mas aqui você mantém sua lógica de RAG
    return f"O Oráculo recebeu sua dúvida: {pergunta}. (Processando via RAG...)"

def enviar_mensagem_whatsapp(to, text):
    """Função para enviar mensagem via API do WhatsApp"""
    url = f"https://graph.facebook.com/v18.0/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WA_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        logger.info(f"Status do envio: {response.status_code}")
        return response.json()
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {e}")
        return None

# --- INICIALIZAÇÃO PARA O RENDER ---
if __name__ == "__main__":
    # Ajuste dinâmico de porta para o Render
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Servidor subindo na porta {port}...")
    app.run(host="0.0.0.0", port=port)
