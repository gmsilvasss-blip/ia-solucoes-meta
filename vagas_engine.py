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
        cidades_excluir = ["Cajamar", "Jarinu", "Jundiaí", "Várzea Paulista", "Barueri", "Osasco"]
        padrao_salario = r"R\$\s?[3-9]\.\d{3}"
        
        vagas_encontradas = []

        status, mensagens = mail.search(None, f'(FROM "{remetente_indeed}")')
        ids = mensagens[0].split()

        if not ids:
            return []

        # Analisamos os e-mails mais recentes
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
            
            for link in soup.find_all('a', href=True):
                url = link['href']
                if "indeed.com" in url and ("clk" in url or "viewjob" in url):
                    container = link.find_parent()
                    texto_bloco = container.get_text(separator=' ') if container else ""
                    
                    # Extração do local real
                    local_bruto = "São Paulo, SP"
                    partes = [p.strip() for p in texto_bloco.split(' - ') if "SP" in p or "São Paulo" in p]
                    if partes:
                        local_bruto = partes[0]

                    match_salario = re.search(padrao_salario, texto_bloco)
                    if match_salario:
                        eh_interior = any(cid.lower() in local_bruto.lower() for cid in cidades_excluir)
                        eh_capital = "são paulo" in local_bruto.lower() or "sp" in local_bruto.lower()

                        if eh_capital and not eh_interior:
                            titulo = link.get_text().strip() or "Vaga Detectada"
                            
                            # Limpeza simples para Android sem encurtador
                            url_final = url.strip().replace("\n", "").replace("\r", "")
                            
                            vaga_msg = (
                                f"📋 *Cargo:* {titulo[:60]}\n"
                                f"💰 *Salário:* {match_salario.group()}\n"
                                f"📍 *Local:* {local_bruto}\n"
                                f"🔗 *Link:* {url_final}"
                            )
                            
                            # REATIVADA A TRAVA DE DUPLICIDADE
                            if vaga_msg not in vagas_encontradas:
                                vagas_encontradas.append(vaga_msg)

        mail.logout()
        # Retorna a lista final sem duplicados
        return vagas_encontradas[:8]

    except Exception as e:
        return [f"Erro na varredura: {str(e)}"]
