import os
import imaplib
import email
from bs4 import BeautifulSoup
import re
from openai import OpenAI # Adicione no requirements.txt

client = OpenAI(api_key=os.environ.get('Openai_Key'))

def executar_varredura_vagas():
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    
    if not user or not password:
        return ["Erro: Credenciais de e-mail não configuradas."]

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user, password)
        mail.select("inbox")

        # Lista de remetentes para multiplataforma
        fontes = {
            "Indeed": "donotreply@match.indeed.com",
            "LinkedIn": "jobalerts-noreply@linkedin.com"
        }

        vagas_finais = []
        locais_alvo = ["Liberdade", "São Paulo", "SP", "Centro", "Paulista", "Bela Vista"]

        for plataforma, remetente in fontes.items():
            status, mensagens = mail.search(None, f'(FROM "{remetente}")')
            ids = mensagens[0].split()

            if not ids: continue

            # Analisa o e-mail mais recente de cada plataforma
            _, data = mail.fetch(ids[-1], "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            
            # Extração de HTML simplificada
            corpo = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        corpo = part.get_payload(decode=True).decode('utf-8', errors='ignore')
            
            soup = BeautifulSoup(corpo, "html.parser")

            # Busca links de vagas (viewjob no Indeed, jobs/view no LinkedIn)
            for link in soup.find_all('a', href=True):
                url = link['href']
                if "clk" in url or "viewjob" in url or "jobs/view" in url:
                    container = link.find_parent()
                    texto_bruto = container.get_text(separator=' ') if container else ""
                    
                    # Filtro inicial de localidade (Ciência de Dados básica)
                    if any(l.lower() in texto_bruto.lower() for l in locais_alvo):
                        # --- CHAMADA À INTELIGÊNCIA ARTIFICIAL ---
                        # A IA vai organizar o texto bagunçado do e-mail
                        analise = processar_vaga_com_ai(texto_bruto, plataforma)
                        
                        vaga_pronta = (
                            f"📋 *{analise['nome']}*\n"
                            f"📍 *Local:* {analise['local']}\n"
                            f"💰 *Salário:* {analise['salario']}\n"
                            f"🏢 *Plataforma:* {plataforma}\n"
                            f"📑 *Regime:* {analise['regime']}\n"
                            f"⏰ *Carga/Modalidade:* {analise['modalidade']}\n"
                            f"🎁 *Benefícios:* {analise['beneficios']}\n"
                            f"🔗 *Link:* {url.split('?')[0]}\n"
                            f"📝 *Descrição:* {analise['descricao'][:200]}..."
                        )
                        vagas_finais.append(vaga_pronta)
        
        mail.logout()
        return vagas_finais[:3] # Limite para não gastar muita API de uma vez

    except Exception as e:
        return [f"Erro na varredura: {str(e)}"]

def processar_vaga_com_ai(texto, plataforma):
    """Usa OpenAI para extrair dados estruturados do texto do e-mail"""
    prompt = f"Extraia os seguintes dados desta vaga de emprego do {plataforma}: Nome da vaga, Localidade, Salário, Regime (CLT/PJ), Modalidade, Benefícios e uma breve Descrição. Texto: {texto}"
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    # Aqui você faria o tratamento do JSON de resposta da IA
    # Por agora, simulamos o retorno estruturado
    return {
        "nome": "Analista de Dados (Exemplo)",
        "local": "São Paulo - Centro",
        "salario": "R$ 4.500",
        "regime": "CLT",
        "modalidade": "Híbrido",
        "beneficios": "VR, VT, Seguro de Vida",
        "descricao": "Vaga focada em automação de processos Python..."
    }
