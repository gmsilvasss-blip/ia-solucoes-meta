import os
import logging
import requests
from flask import Flask, request, jsonify, render_template
from apscheduler.schedulers.background import BackgroundScheduler
from vagas_engine import executar_varredura_vagas  # Importa sua engine de busca
from dotenv import load_dotenv

# Carrega variáveis de ambiente (local do .env, no Render do painel)
load_dotenv()

# Configuração de Logs para acompanhamento no Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='.')

# --- VARIÁVEIS DE AMBIENTE (Padrão Guilherme) ---
APP_ID = os.environ.get('App_Id')
WA_TOKEN = os.environ.get('WHATSAPP_TOKEN')
PHONE_ID = os.environ.get('PHONE_NUMBER_ID')
VERIFY_TOKEN = os.environ.get('Verify_Token_Webhook', 'webhookkey')

# Novas variáveis para a automação e IA
MEU_NUMERO = os.environ.get('Meu_Numero_Whatsapp')
AI_API_KEY = os.environ.get('Openai_Key')

@app.route('/')
def home():
    """Página inicial do projeto"""
    return render_template('index.html', app_id=APP_ID)

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # Validação do Webhook (GET)
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        return 'Forbidden', 403

    # Recebimento de Mensagens (POST)
    if request.method == 'POST':
        data = request.json
        if is_valid_message(data):
            msg_body = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
            from_number = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
            
            # Chama o Oráculo (Lógica de RAG mantida)
            resposta_ia = processar_oraculo(msg_body)
            
            # Envia a resposta da IA (Removido o eco simples)
            enviar_mensagem_whatsapp(from_number, resposta_ia)

        return jsonify({"status": "ok"}), 200

def is_valid_message(data):
    try:
        return 'messages' in data['entry'][0]['changes'][0]['value']
    except:
        return False

def processar_oraculo(pergunta):
    """Lógica do Oráculo com IA"""
    logger.info(f"Processando pergunta: {pergunta}")
    # Aqui você mantém sua implementação de busca no banco vetorial/RAG
    return f"O Oráculo recebeu sua dúvida: {pergunta}. (Processando via RAG...)"

def enviar_mensagem_whatsapp(to, text):
    """Envia mensagens via API da Meta"""
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
        logger.info(f"Status do envio para {to}: {response.status_code}")
        return response.json()
    except Exception as e:
        logger.error(f"Erro ao enviar WhatsApp: {e}")

# --- AUTOMAÇÃO DE VAGAS ---

def tarefa_diaria_vagas():
    """Executa a varredura no e-mail e envia o relatório se encontrar vagas"""
    logger.info("Iniciando varredura programada de vagas...")
    vagas = executar_varredura_vagas()
    
    if vagas:
        # Envia um cabeçalho primeiro
        enviar_mensagem_whatsapp(MEU_NUMERO, "💼 *Relatório de Vagas Selecionadas (Indeed)*")
        # Envia cada vaga individualmente para não estourar o limite de caracteres
        for vaga in vagas:
            enviar_mensagem_whatsapp(MEU_NUMERO, vaga)
    else:
        logger.info("Nenhuma vaga acima de R$ 3.000 encontrada hoje.")

# Agendador (Roda em paralelo ao Flask)
scheduler = BackgroundScheduler()
# Configurado para 12:00 UTC (Aproximadamente 09:00 Horário de Brasília/Jundiaí)
#scheduler.add_job(tarefa_diaria_vagas, 'cron', hour=12, minute=0)
scheduler.add_job(tarefa_diaria_vagas, 'date')
scheduler.start()

if __name__ == "__main__":
    # O Render define a porta automaticamente
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

