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
        
        # Lista de cidades que você quer IGNORAR (Lista Negra)
        cidades_excluir = [
            "Cajamar", "Jarinu", "Jundiaí", "Várzea Paulista", "Barueri", 
            "Osasco", "Guarulhos", "Campinas", "Santana de Parnaíba", "Itapevi"
        ]
        
        padrao_salario = r"R\$\s?[3-9]\.\d{3}"
        vagas_encontradas = []

        status, mensagens = mail.search(None, f'(FROM "{remetente_indeed}")')
        ids = mensagens[0].split()

        if not ids: return []

        # Analisamos o e-mail mais recente
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
        
        for link in soup.find_all('a', href=True):
            url = link['href']
            
            if "indeed.com" in url and ("clk" in url or "viewjob" in url):
                container = link.find_parent()
                texto_bloco = container.get_text(separator=' ') if container else ""
                
                # 1. Validação de Salário
                match_salario = re.search(padrao_salario, texto_bloco)
                
                if match_salario:
                    # 2. Extração da Localização Real
                    local_encontrado = "São Paulo, SP" # Valor padrão
                    
                    # O Indeed geralmente separa Local por " - " ou coloca após o nome da empresa
                    # Vamos buscar a parte que contém "SP" ou "São Paulo"
                    partes = [p.strip() for p in texto_bloco.split(' - ') if "SP" in p or "São Paulo" in p]
                    if partes:
                        local_encontrado = partes[0]

                    # 3. Filtro de Capital vs Interior
                    # Só aceitamos se contiver "São Paulo" e NÃO contiver cidades da lista negra
                    eh_interior = any(cid.lower() in local_encontrado.lower() for cid in cidades_excluir)
                    eh_capital = "são paulo" in local_encontrado.lower() or "sp" in local_encontrado.lower()

                    if eh_capital and not eh_interior:
                        titulo = link.get_text().strip()
                        if len(titulo) < 3: titulo = "Vaga Identificada"

                        vaga_msg = (
                            f"📋 *Cargo:* {titulo[:60]}\n"
                            f"💰 *Salário:* {match_salario.group()}\n"
                            f"📍 *Local:* {local_encontrado}\n"
                            f"🏢 *Plataforma:* Indeed\n"
                            f"🔗 *Link:* {url}"
                        )
                        
                        if vaga_msg not in vagas_encontradas:
                            vagas_encontradas.append(vaga_msg)

        mail.logout()
        return vagas_encontradas[:8] # Aumentei para 8 vagas já que o raio é maior

    except Exception as e:
        return [f"Erro na varredura: {str(e)}"]
