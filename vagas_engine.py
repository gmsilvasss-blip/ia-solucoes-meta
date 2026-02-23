import os
import imaplib
import email
from bs4 import BeautifulSoup
import re

def executar_varredura_vagas():
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    
    if not user or not password:
        return ["Erro: Credenciais de e-mail não configuradas."]

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user, password)
        mail.select("inbox")

        # Configuração das fontes baseada nos seus anexos
        fontes = {
            "Indeed": "donotreply@match.indeed.com",
            "Glassdoor": "noreply@glassdoor.com",
            "Catho": "sugestaovagas@catho.com.br"
        }
        
        cidades_excluir = ["Cajamar", "Jarinu", "Jundiaí", "Várzea Paulista", "Barueri", "Osasco", "Mogi das Cruzes"]
        padrao_salario = r"R\$\s?[3-9]\.\d{3}"
        vagas_encontradas = []

        for plataforma, remetente in fontes.items():
            status, mensagens = mail.search(None, f'(FROM "{remetente}")')
            ids = mensagens[0].split()
            if not ids: continue

            # Analisa os 2 e-mails mais recentes de cada fonte
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
                
                # Extração por Plataforma
                for link in soup.find_all('a', href=True):
                    url = link['href']
                    container = link.find_parent()
                    texto_bloco = container.get_text(separator=' ') if container else ""
                    
                    # Filtro de Localidade (Qualquer bairro em SP capital)
                    eh_capital = "são paulo" in texto_bloco.lower() or "sp" in texto_bloco.lower()
                    eh_interior = any(cid.lower() in texto_bloco.lower() for cid in cidades_excluir)
                    
                    if eh_capital and not eh_interior:
                        titulo = link.get_text().strip()
                        # Se o título for curto (ex: "Candidatura rápida"), tenta pegar o texto ao redor
                        if len(titulo) < 5 and container:
                            titulo = container.get_text().split('\n')[0].strip()

                        # Identifica Salário (Se não tiver, marca como 'A combinar')
                        match_salario = re.search(padrao_salario, texto_bloco)
                        salario = match_salario.group() if match_salario else "A combinar"

                        vaga_msg = (
                            f"📋 *Cargo:* {titulo[:60]}\n"
                            f"💰 *Salário:* {salario}\n"
                            f"📍 *Local:* São Paulo, SP\n"
                            f"🏢 *Plataforma:* {plataforma}\n"
                            f"🔗 *Link:* {url.strip()}"
                        )

                        if vaga_msg not in vagas_encontradas:
                            vagas_encontradas.append(vaga_msg)

        mail.logout()
        return vagas_encontradas[:10]

    except Exception as e:
        return [f"Erro na varredura: {str(e)}"]
