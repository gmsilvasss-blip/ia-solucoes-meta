import os
import imaplib
import email
from bs4 import BeautifulSoup
import re

def executar_varredura_vagas():
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    
    if not user or not password:
        return ["Erro: Credenciais de e-mail não configuradas no Render."]

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user, password)
        mail.select("inbox")

        # Configuração de Fontes e Filtros
        fontes = {
            "Indeed": "donotreply@match.indeed.com",
            "LinkedIn": "jobalerts-noreply@linkedin.com"
        }
        locais_alvo = ["Liberdade", "São Paulo", "SP", "Centro", "Paulista", "Bela Vista"]
        padrao_salario = r"R\$\s?[3-9]\.\d{3}"
        
        vagas_finais = []

        for plataforma, remetente in fontes.items():
            status, mensagens = mail.search(None, f'(FROM "{remetente}")')
            ids = mensagens[0].split()
            if not ids: continue

            # Analisamos os 2 e-mails mais recentes de cada fonte
            for e_id in ids[-2:]:
                _, data = mail.fetch(e_id, "(RFC822)")
                msg = email.message_from_bytes(data[0][1])
                
                corpo_html = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/html":
                            corpo_html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                else:
                    corpo_html = msg.get_payload(decode=True).decode('utf-8', errors='ignore')

                soup = BeautifulSoup(corpo_html, "html.parser")
                
                # Buscamos os blocos de vagas
                for link in soup.find_all('a', href=True):
                    url = link['href']
                    # Filtro de links de vaga reais
                    if "clk" in url or "viewjob" in url or "jobs/view" in url:
                        container = link.find_parent()
                        # Pegamos o texto limpo do bloco da vaga
                        linhas = [l.strip() for l in container.get_text(separator='\n').split('\n') if l.strip()]
                        texto_bloco = " ".join(linhas)
                        
                        # Validação de Localidade e Salário
                        tem_local = any(l.lower() in texto_bloco.lower() for l in locais_alvo)
                        match_salario = re.search(padrao_salario, texto_bloco)

                        if tem_local and match_salario:
                            # Tentativa de extrair título (geralmente a primeira linha do bloco)
                            titulo = linhas[0] if len(linhas) > 0 else "Título não identificado"
                            salario = match_salario.group()
                            
                            vaga_msg = (
                                f"📋 *Cargo:* {titulo}\n"
                                f"📍 *Local:* SP (Foco Centro/Liberdade)\n"
                                f"💰 *Salário:* {salario}\n"
                                f"🏢 *Plataforma:* {plataforma}\n"
                                f"🔗 *Link:* {url.split('?')[0]}\n"
                                f"--------------------------"
                            )
                            
                            if vaga_msg not in vagas_finais:
                                vagas_finais.append(vaga_msg)

        mail.logout()
        return vagas_finais[:6] # Retorna até 6 vagas para o relatório

    except Exception as e:
        return [f"Erro na varredura: {str(e)}"]
