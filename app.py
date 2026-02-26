import os
import requests
import json
from flask import Flask, request, render_template
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from vagas_engine import executar_varredura_vagas

# Configurado para ler HTML da raiz do projeto (.)
app = Flask(__name__, template_folder='.')

# --- ROTAS DE FACHADA E CONFORMIDADE (META) ---

@app.route("/", methods=['GET'])
def home():
    # Carrega a página inicial oficial com o botão de login e rodapé
    app_id = os.getenv("App_Id")
    return render_template('index.html', app_id=app_id)

@app.route("/politica_privacidade", methods=['GET'])
def politica_privacidade():
    # Rota exigida pela Meta para os Termos de Privacidade
    return render_template('politica_privacidade.html')

@app.route("/exclusao", methods=['GET'])
def exclusao():
    # Rota exigida pela Meta para instruções de exclusão de dados
    return render_template('exclusao.html')

# --- FUNÇÃO DE ENVIO REAL ---
def enviar_mensagem_whatsapp(mensagem):
    token = os.getenv("WHATSAPP_TOKEN")
    phone_number_id = os.getenv("PHONE_NUMBER_ID")
    meu_numero = os.getenv("Meu_Numero_Whatsapp")

    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": meu_numero,
        "type": "text",
        "text": {"body": mensagem}
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"INFO:app:Status do envio: {response.status_code}")
        return response.status_code
    except Exception as e:
        print(f"ERRO:app:Falha ao enviar: {str(e)}")
        return 500

def gerar_resumo_estrategico():
    return "💡 O Oráculo está em modo de demonstração para análise da Meta."

# --- AGENDADOR (PAUSADO PARA O VÍDEO) ---
# Comentei o scheduler para garantir que nada rode sozinho durante o seu vídeo
# scheduler = BackgroundScheduler()
# scheduler.add_job(executar_varredura_vagas, CronTrigger(minute='0,30'))
# scheduler.start()

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

    # Recebimento de Mensagens
    data = request.get_json()
    try:
        if 'messages' in data['entry'][0]['changes'][0]['value']:
            msg_obj = data['entry'][0]['changes'][0]['value']['messages'][0]
            texto_usuario = msg_obj.get('text', {}).get('body', "").lower()

            # Resposta para o Vídeo (Simulando o Template hello_world)
            if any(cmd in texto_usuario for cmd in ["vaga", "vagas", "oi", "ola"]):
                # TEXTO EXATO DO TEMPLATE QUE VOCÊ MOSTROU NO PAINEL
                template_text = "Welcome and congratulations! This message confirms that your integration with the WhatsApp Business Platform is working correctly."
                enviar_mensagem_whatsapp(template_text)
            
            elif "resumo" in texto_usuario:
                enviar_mensagem_whatsapp(gerar_resumo_estrategico())
                
    except Exception as e:
        print(f"Erro no webhook: {e}")
        pass
    return "EVENT_RECEIVED", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
