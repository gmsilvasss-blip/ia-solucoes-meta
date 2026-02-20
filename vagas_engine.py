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

        # Configurações de busca
        remetente_indeed = "donotreply@match.indeed.com"
        locais_alvo = ["Liberdade", "São Paulo", "SP", "Centro", "Paulista", "Bela Vista"]
        padrao_salario = r"R\$\s?[3-9]\.\d{3}"
        
        vagas_encontradas = []

        # Busca apenas no Indeed por enquanto
        status, mensagens = mail.search(None, f'(FROM "{remetente_indeed}")')
        ids = mensagens[0].split()

        if not ids:
            return []

        # Analisamos os e-mails mais recentes
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
            
            # Varredura de links reais de vagas
            for link in soup.find_all('a', href=True):
                url = link['href']
                
                # O Indeed usa 'clk' ou 'viewjob' para os links de candidatura
                if "clk" in url or "viewjob" in url:
                    container = link.find_parent()
                    texto_bloco = container.get_text(separator=' ') if container else ""
                    
                    # Filtro Geográfico e Salarial
                    match_local = any(l.lower() in texto_bloco.lower() for l in locais_alvo)
                    match_salario = re.search(padrao_salario, texto_bloco)

                    if match_local and match_salario:
                        # Extração do Título (Texto dentro do link ou do container)
                        titulo = link.get_text().strip() or container.find().get_text().strip()
                        salario = match_salario.group()
                        
                        # Montagem da mensagem limpa
                        vaga_msg = (
                            f"📋 *Cargo:* {titulo[:50]}\n"
                            f"💰 *Salário:* {salario}\n"
                            f"📍 *Local:* São Paulo (Região Central)\n"
                            f"🏢 *Plataforma:* Indeed\n"
                            f"🔗 *Link:* {url.split('?')[0]}"
                        )
                        
                        if vaga_msg not in vagas_encontradas:
                            vagas_encontradas.append(vaga_msg)

        mail.logout()
        return vagas_encontradas[:5] # Retorna apenas dados REAIS encontrados

    except Exception as e:
        return [f"Erro na varredura: {str(e)}"]
