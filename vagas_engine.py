import os
import imaplib
import email
from bs4 import BeautifulSoup
import re

def executar_varredura_vagas():
    """
    Motor de busca focado em SP/Liberdade e extração de links.
    """
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    
    if not user or not password:
        return ["Erro: Credenciais de e-mail não configuradas no Render."]

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user, password)
        mail.select("inbox")

        # Busca e-mails do Indeed
        status, mensagens = mail.search(None, '(FROM "donotreply@match.indeed.com")')
        ids = mensagens[0].split()

        if not ids:
            return []

        # Analisamos os 3 e-mails mais recentes para evitar perdas
        vagas_filtradas = []
        locais_alvo = ["Liberdade", "São Paulo", "SP", "Centro", "Paulista", "Bela Vista"]
        padrao_salario = r"R\$\s?[3-9]\.\d{3}"

        for e_id in ids[-3:]:
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
            
            # Buscamos todos os links que podem ser de vagas
            for link in soup.find_all('a', href=True):
                url = link['href']
                # O Indeed usa 'viewjob' ou 'jk=' nos links de vaga específicos
                if "clk" in url or "viewjob" in url:
                    # Pegamos o texto ao redor do link para validar local e salário
                    container = link.find_parent()
                    texto_contexto = container.get_text() if container else ""
                    
                    # Filtro de Localidade + Salário
                    tem_local = any(local.lower() in texto_contexto.lower() for local in locais_alvo)
                    match_salario = re.search(padrao_salario, texto_contexto)

                    if tem_local and match_salario:
                        salario = match_salario.group()
                        vaga_formatada = (
                            f"📍 *Oportunidade em SP (Foco Liberdade)*\n"
                            f"💰 *Salário:* {salario}\n"
                            f"🔗 *Link:* {url.split('?')[0]}" # Limpa o link de rastreio pesado
                        )
                        
                        if vaga_formatada not in vagas_filtradas:
                            vagas_filtradas.append(vaga_formatada)

        mail.logout()
        # Retorna apenas as 5 primeiras para não sobrecarregar o WhatsApp de uma vez
        return vagas_filtradas[:5]

    except Exception as e:
        return [f"Erro na varredura: {str(e)}"]
