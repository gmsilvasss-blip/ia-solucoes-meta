import os
import imaplib
import email
from bs4 import BeautifulSoup
import re

def salvar_no_historico(titulo, texto_bloco):
    """Armazena os detalhes da vaga para análise de requisitos futura."""
    try:
        # O modo 'a' (append) adiciona ao final do arquivo sem apagar o anterior
        with open("historico_vagas.txt", "a", encoding="utf-8") as f:
            # Limpamos quebras de linha para manter o log organizado
            conteudo_limpo = texto_bloco.replace("\n", " ").strip()
            f.write(f"VAGA: {titulo} | CONTEUDO: {conteudo_limpo[:600]}\n")
    except Exception as e:
        print(f"Erro ao salvar histórico: {e}")

def executar_varredura_vagas():
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    
    if not user or not password:
        return ["Erro: Credenciais não configuradas."]

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user, password)
        mail.select("inbox")

        fontes = {
            "Indeed": "donotreply@match.indeed.com",
            "Glassdoor": "noreply@glassdoor.com",
            "Catho": "sugestaovagas@catho.com.br"
        }
        
        cidades_excluir = ["Cajamar", "Jarinu", "Jundiaí", "Várzea Paulista", "Barueri", "Osasco"]
        padrao_salario = r"R\$\s?[3-9]\.\d{3}"
        vagas_encontradas = []

        for plataforma, remetente in fontes.items():
            status, mensagens = mail.search(None, f'(FROM "{remetente}")')
            ids = mensagens[0].split()
            if not ids: continue

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
                
                for link in soup.find_all('a', href=True):
                    url = link['href']
                    container = link.find_parent()
                    texto_bloco = container.get_text(separator=' ') if container else ""
                    
                    eh_capital = "são paulo" in texto_bloco.lower() or "sp" in texto_bloco.lower()
                    eh_interior = any(cid.lower() in texto_bloco.lower() for cid in cidades_excluir)
                    
                    if eh_capital and not eh_interior:
                        titulo = link.get_text().strip()
                        if len(titulo) < 5 and container:
                            titulo = container.get_text().split('\n')[0].strip()

                        match_salario = re.search(padrao_salario, texto_bloco)
                        salario = match_salario.group() if match_salario else "A combinar"

                        vaga_msg = (
                            f"📋 *Cargo:* {titulo[:60]}\n"
                            f"💰 *Salário:* {salario}\n"
                            f"📍 *Local:* São Paulo, SP\n"
                            f"🏢 *Plataforma:* {plataforma}\n"
                            f"🔗 *Link:* {url.strip().replace('\\n', '')}"
                        )

                        if vaga_msg not in vagas_encontradas:
                            vagas_encontradas.append(vaga_msg)
                            # Salva para o resumo de softskills/certificações
                            salvar_no_historico(titulo, texto_bloco)

        mail.logout()
        return vagas_encontradas[:8]

    except Exception as e:
        return [f"Erro na varredura: {str(e)}"]
