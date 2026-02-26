import os
import requests
import json
from flask import Flask, request, render_template
# Importação mantida para o projeto estar íntegro
from vagas_engine import executar_varredura_vagas 

# Configurado para ler HTML da raiz do projeto (.)
app = Flask(__name__, template_folder='.')

# --- ROTAS DE FACHADA E CONFORMIDADE (META) ---

@app.route("/", methods=['GET'])
def home():
    app_id = os.getenv("App_Id")
    return render_template('index.html', app_id=app_id)

@app.route("/politica_privacidade", methods=['GET'])
def privacidade():
    return render_template('politica_privacidade.html')

@app.route("/exclusao", methods=['GET'])
def exclusao():
    return render_template('exclusao.html')

# --- FUNÇÃO DE ENVIO DINÂMICA (Responde para quem mandou) ---
def enviar_resposta_dinamica(destinatario, mensagem):
    token = os.getenv("WHATSAPP_TOKEN")
    phone_number_id = os.getenv("PHONE_NUMBER_ID")
    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": destinatario,
        "type": "text",
        "text": {"body": mensagem}
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"INFO:app:Status do envio para {destinatario}: {response.status_code}")
        return response.status_code
    except Exception as e:
        print(f"ERRO:app:Falha ao enviar: {str(e)}")
        return 500

# --- O ORQUESTRADOR (PAUSADO PARA O VÍDEO) ---
# O código continua aqui, mas não iniciamos o scheduler agora para evitar spam no vídeo
# def iniciar_agendador():
#     from apscheduler.schedulers.background import BackgroundScheduler
#     from apscheduler.triggers.cron import CronTrigger
#     scheduler = BackgroundScheduler()
#     scheduler.add_job(executar_varredura_vagas, CronTrigger(minute='0,30'))
#     scheduler.start()

# --- WEBHOOK (INTERFACE COM WHATSAPP) ---
@app.route("/webhook", methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        verify_token = os.getenv("Verify_Token_Webhook")
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if mode == 'subscribe' and token == verify_token:
            return challenge, 200
        return 'Forbidden', 403

    data = request.get_json()
    print(f"DEBUG: Dados recebidos da Meta: {json.dumps(data)}")

    try:
        if 'messages' in data['entry'][0]['changes'][0]['value']:
            msg_obj = data['entry'][0]['changes'][0]['value']['messages'][0]
            remetente = msg_obj.get('from') 
            texto_usuario = msg_obj.get('text', {}).get('body', "").lower()

            # Resposta para o Vídeo (Simulando o Template hello_world)
            if any(cmd in texto_usuario for cmd in ["vaga", "vagas", "oi", "ola", "olá"]):
                template_text = "Welcome and congratulations! This message confirms that your integration with the WhatsApp Business Platform is working correctly."
                enviar_resposta_dinamica(remetente, template_text)
            
            elif "resumo" in texto_usuario:
                resumo = "💡 O Oráculo está monitorizando vagas (Modo de Demonstração)."
                enviar_resposta_dinamica(remetente, resumo)
                
    except Exception as e:
        print(f"ERRO:app:Erro no webhook: {e}")
    
    return "EVENT_RECEIVED", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
