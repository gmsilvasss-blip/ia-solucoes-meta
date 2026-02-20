import os
import imaplib
import email
from bs4 import BeautifulSoup
import re

def executar_varredura_vagas():
    """
    Função principal que conecta ao Gmail, filtra vagas do Indeed 
    e retorna uma lista de mensagens formatadas.
    """
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    
    if not user or not password:
        return ["Erro: Credenciais de e-mail não configuradas no Render."]

    try:
        # 1. Conexão Segura
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user, password)
        mail.select("inbox")

        # 2. Busca e-mails do Indeed (Remetente do seu PDF) [cite: 1, 6]
        # Filtramos e-mails de hoje ou recentes
        status, mensagens = mail.search(None, '(FROM "donotreply@match.indeed.com")')
        ids = mensagens[0].split()

        if not ids:
            return []

        # Pega o e-mail mais recente [cite: 8]
        ultimo_id = ids[-1]
        _, data = mail.fetch(ultimo_id, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])

        # 3. Extração do Conteúdo
        corpo_html = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    corpo_html = part.get_payload(decode=True).decode()
                    break
        else:
            corpo_html = msg.get_payload(decode=True).decode()

        # 4. Parsing e Mineração de Dados (Ciência de Dados)
        soup = BeautifulSoup(corpo_html, "html.parser")
        texto_limpo = soup.get_text(separator='\n')

        # Regex para identificar blocos de vaga (Título + Empresa + Salário)
        # Baseado no padrão: Título da Vaga -> Empresa -> Salário [cite: 11, 12, 13]
        vagas_encontradas = []
        
        # Padrão para capturar salários atraentes (acima de R$ 3.000) 
        # Procura R$ seguido de 3, 4, 5... para bater sua meta.
        padrao_salario = r"R\$\s?[3-9]\.\d{3}" 
        
        # Aqui simulamos a extração de blocos (Aperfeiçoe conforme a estrutura do HTML)
        linhas = [l.strip() for l in texto_limpo.split('\n') if l.strip()]
        
        for i, linha in enumerate(linhas):
            if "R$" in linha:
                salario_match = re.search(padrao_salario, linha)
                if salario_match:
                    # Tenta pegar o título (geralmente 2 linhas antes do salário no Indeed)
                    titulo = linhas[i-2] if i > 1 else "Vaga Encontrada"
                    empresa = linhas[i-1] if i > 0 else "Empresa não identificada"
                    
                    vaga_formatada = (
                        f"🚀 *Oportunidade Detectada!*\n"
                        f"📌 *Cargo:* {titulo}\n"
                        f"🏢 *Empresa:* {empresa}\n"
                        f"💰 *Salário:* {linha}\n"
                        f"🔗 [Candidate-se no Indeed]"
                    )
                    vagas_encontradas.append(vaga_formatada)

        mail.logout()
        return vagas_encontradas

    except Exception as e:
        return [f"Erro técnico na varredura: {str(e)}"]

if __name__ == "__main__":
    # Teste local
    print(executar_varredura_vagas())
