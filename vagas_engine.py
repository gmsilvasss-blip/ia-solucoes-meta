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

        remetente_indeed = "donotreply@match.indeed.com"
        locais_alvo = ["Liberdade", "São Paulo", "SP", "Centro", "Paulista", "Bela Vista"]
        padrao_salario = r"R\$\s?[3-9]\.\d{3}"
        
        vagas_encontradas = []

        status, mensagens = mail.search(None, f'(FROM "{remetente_indeed}")')
        ids = mensagens[0].split()

        if not ids:
            return []

        # Analisamos apenas o e-mail mais recente para evitar duplicatas pesadas
        _, data = mail.fetch(ids[-1], "(RFC822)")
        msg = email.message_from_bytes(data[0][1])
        
        corpo_html = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    corpo_html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            corpo_html = msg.get_payload(decode=True).decode('utf-8', errors='ignore')

        soup = BeautifulSoup(corpo_html, "html.parser")
        
        # Estratégia: Buscar todos os links que contenham padrões de vaga do Indeed
        for link in soup.find_all('a', href=True):
            url = link['href']
            
            # Verificamos se é um link de vaga (clk, pagead ou viewjob)
            if "indeed.com" in url and ("clk" in url or "viewjob" in url or "pagead" in url):
                container = link.find_parent()
                texto_bloco = container.get_text(separator=' ') if container else ""
                
                # Filtros de Meta
                match_local = any(l.lower() in texto_bloco.lower() for l in locais_alvo)
                match_salario = re.search(padrao_salario, texto_bloco)

                if match_local and match_salario:
                    # Melhoria na captura do Título: pega o texto do link ou do elemento forte mais próximo
                    titulo = link.get_text().strip()
                    if not titulo or len(titulo) < 3:
                        titulo = container.find(['b', 'strong', 'span']).get_text().strip() if container else "Vaga Detectada"
                    
                    salario = match_salario.group()
                    
                    # IMPORTANTE: Não cortamos a URL aqui para não quebrar o redirecionamento do Indeed
                    vaga_msg = (
                        f"📋 *Cargo:* {titulo[:60]}\n"
                        f"💰 *Salário:* {salario}\n"
                        f"📍 *Local:* SP (Região FMU/Centro)\n"
                        f"🔗 *Link:* {url}"
                    )
                    
                    if vaga_msg not in vagas_encontradas:
                        vagas_encontradas.append(vaga_msg)

        mail.logout()
        return vagas_encontradas[:5]

    except Exception as e:
        return [f"Erro na varredura: {str(e)}"]
