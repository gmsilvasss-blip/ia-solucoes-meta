import os
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from vagas_engine import executar_varredura_vagas

app = Flask(__name__)

def gerar_resumo_estrategico():
    """Analisa o gap entre o histórico de vagas e o seu currículo."""
    try:
        if not os.path.exists("historico_vagas.txt") or not os.path.exists("curriculo.txt"):
            return "⚠️ Ainda não tenho dados suficientes (historico ou curriculo) para o resumo."

        with open("historico_vagas.txt", "r", encoding="utf-8") as f:
            vagas = f.read().lower()
        with open("curriculo.txt", "r", encoding="utf-8") as f:
            cv = f.read().lower()

        # Lista de Skills relevantes para Ciência de Dados
        mapa_skills = {
            "PYTHON": "📜 Dica: Fortalecer lógica em Python ou bibliotecas Pandas/Numpy.",
            "SQL": "📊 Dica: Praticar queries complexas e JOINS.",
            "POWER BI": "📉 Dica: Criar um projeto de Dashboard para o portfólio.",
            "INGLÊS": "🌍 Dica: Focar em vocabulário técnico para reuniões.",
            "SPARK": "⚡ Dica: Estudar processamento distribuído (PySpark).",
            "MACHINE LEARNING": "🤖 Dica: Estudar modelos de regressão e classificação."
        }
        
        recomendacoes = []
        for skill, dica in mapa_skills.items():
            # Se a skill aparece nas vagas mas NÃO no seu currículo
            if skill.lower() in vagas and skill.lower() not in cv:
                recomendacoes.append(dica)

        if not recomendacoes:
            return "⭐ *Resumo:* Seu currículo está bem alinhado com as vagas recentes!"
        
        resumo = "📈 *Análise de Gap de Carreira*\nBaseado nas últimas vagas, foque em:\n\n" + "\n".join(recomendacoes)
        return resumo
    except Exception as e:
        return f"Erro ao gerar resumo: {str(e)}"

def job_vagas_manha():
    """Disparo automático às 08:00 AM."""
    vagas = executar_varredura_vagas()
    # Aqui entra sua função de envio: for v in vagas: enviar_wpp(v)

# Configura o agendador para o fuso de São Paulo
scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")
scheduler.add_job(job_vagas_manha, CronTrigger(hour=8, minute=0))
scheduler.start()

@app.route("/webhook", methods=['POST'])
def webhook():
    data = request.get_json()
    try:
        msg = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body'].lower()
        
        if "resumo" in msg:
            feedback = gerar_resumo_estrategico()
            # enviar_wpp(feedback)
            return "OK", 200
            
        if any(cmd in msg for cmd in ["vaga", "oi", "vagas"]):
            vagas = executar_varredura_vagas()
            # for v in vagas: enviar_wpp(v)
            return "OK", 200
    except:
        pass
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
