import os
import logging
import requests
from flask import Flask, request, jsonify, render_template
from apscheduler.schedulers.background import BackgroundScheduler
from vagas_engine import executar_varredura_vagas  # Importa sua nova engine
from dotenv import load_dotenv

# Carrega variáveis locais
load_dotenv()

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='.')

# --- VARIÁVEIS DE AMBIENTE ---
pljx vncx ezdg sehk

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
        return 'Forbidden', 403

    if request.method == 'POST':
        data = request.json
        if is_valid_message(data):
            msg_body = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
            from_number = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
            
            # Mantém a função do Oráculo
            resposta_ia = processar_oraculo(msg_body)
            enviar_mensagem_whatsapp(from_number, resposta_ia)

        return jsonify({"status": "ok"}), 200

def is_valid_message(data):
    try:
        return 'messages' in data['entry'][0]['changes'][0]['value']
    except:
        return False

def processar_oraculo(pergunta):
    logger.info(f"Oráculo consultado: {pergunta}")
    # Aqui continua sua lógica de RAG original
    return f"O Oráculo está analisando: {pergunta}"

def enviar_mensagem_whatsapp(to, text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WA_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
    except Exception as e:
        logger.error(f"Erro ao enviar: {e}")

# --- NOVA FUNÇÃO: TAREFA AGENDADA ---
def tarefa_diaria_vagas():
    """Chama a engine de vagas e envia para o seu WhatsApp"""
    logger.info("Iniciando varredura diária de vagas...")
    vagas = executar_varredura_vagas()
    
    if vagas:
        enviar_mensagem_whatsapp(MEU_NUMERO, "🔔 *Relatório Diário de Vagas (Indeed)*")
        for vaga in vagas:
            enviar_mensagem_whatsapp(MEU_NUMERO, vaga)
    else:
        logger.info("Nenhuma vaga encontrada no critério hoje.")

# Configuração do Agendador (Roda em segundo plano)
scheduler = BackgroundScheduler()
# Configurado para rodar todo dia às 09:00 (Horário do servidor)
# Você pode ajustar para 'interval' e minutes=60 se preferir testar rápido
scheduler.add_job(tarefa_diaria_vagas, 'cron', hour=12, minute=0)
scheduler.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

