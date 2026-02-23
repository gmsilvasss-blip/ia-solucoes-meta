import os
import requests
import json
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from vagas_engine import executar_varredura_vagas

app = Flask(__name__)

# --- FUNÇÃO DE ENVIO REAL (USANDO TUAS VARIÁVEIS DO RENDER) ---
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
        print(f"INFO:app:Status do envio para {meu_numero}:{response.status_code}")
        return response.status_code
    except Exception as e:
        print(f"ERRO:app:Falha ao enviar mensagem: {str(e)}")
        return 500

# --- LÓGICA DE RESUMO ESTRATÉGICO ---
def gerar_resumo_estrategico():
    try:
        if not os.path.exists("historico_vagas.txt") or not os.path.exists("curriculo.txt"):
            return "⚠️ Ainda não tenho dados históricos ou o teu arquivo 'curriculo.txt' para gerar o resumo."

        with open("historico_vagas.txt", "r", encoding="utf-8") as f:
            vagas = f.read().lower()
        with open("curriculo.txt", "r", encoding="utf-8") as f:
            cv = f.read().lower()

        mapa_skills = {
            "python": "📜 Dica: Fortalecer lógica em Python ou bibliotecas Pandas/Numpy.",
            "sql": "📊 Dica: Praticar queries complexas e JOINS.",
            "power bi": "📉 Dica: Criar um projeto de Dashboard para o portfólio.",
            "inglês": "🌍 Dica: Focar em vocabulário técnico para reuniões.",
            "pyspark": "⚡ Dica: Estudar processamento distribuído (PySpark).",
            "machine learning": "🤖 Dica: Estudar modelos de regressão e classificação."
        }
        
        recomendacoes = []
        for skill, dica in mapa_skills.items():
            if skill in vagas and skill not in cv:
                recomendacoes.append(dica)

        if not recomendacoes:
            return "⭐ *Resumo:* O teu currículo está muito bem alinhado com as vagas recentes!"
        
        return "📈 *Análise de Gap de Carreira*\nCom base nas vagas analisadas, foca em:\n\n" + "\n".join(recomendacoes)
    except Exception as e:
        return f"Erro ao processar resumo: {str(e)}"

# --- AGENDADOR (SCHEDULER) ---
def job_vagas_manha():
    print("🌅 Iniciando varredura matinal automática...")
    vagas = executar_varredura_vagas()
    if vagas:
        for v in vagas:
            enviar_mensagem_whatsapp(v)

scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")
scheduler.add_job(job_vagas_manha, CronTrigger(hour=8, minute=0))
scheduler.start()

# --- WEBHOOK (GATILHOS MANUAIS) ---
@app.route("/webhook", methods=['GET', 'POST'])
def webhook():
    # Verificação de Token da Meta (Configuração Inicial)
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

            # Gatilho: RESUMO
            if "resumo" in texto_usuario:
                enviar_mensagem_whatsapp(gerar_resumo_estrategico())
            
            # Gatilho: VARREDURA IMEDIATA
            elif any(cmd in texto_usuario for cmd in ["vaga", "vagas", "oi"]):
                vagas = executar_varredura_vagas()
                if not vagas:
                    enviar_mensagem_whatsapp("Nenhuma nova vaga encontrada agora.")
                else:
                    for v in vagas:
                        enviar_mensagem_whatsapp(v)
    except:
        pass
    return "EVENT_RECEIVED", 200

@app.route("/", methods=['GET'])
def home():
    return "Oráculo de Vagas Ativo", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
