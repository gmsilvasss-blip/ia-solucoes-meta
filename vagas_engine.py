import imaplib
import email
from bs4 import BeautifulSoup
import re

def conectar_email(usuario, senha):
    # Conecta ao servidor IMAP do Gmail
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(usuario, senha)
    return mail

def buscar_vagas_indeed(mail):
    # Seleciona a caixa de entrada
    mail.select("inbox")
    
    # Busca e-mails do remetente específico do Indeed
    # O remetente no seu PDF é donotreply@match.indeed.com
    status, mensagens = mail.search(None, '(FROM "donotreply@match.indeed.com")')
    
    lista_vagas = []
    
    # Pega apenas os IDs dos e-mails encontrados
    ids = mensagens[0].split()
    
    # Vamos processar apenas o e-mail mais recente para testar
    if ids:
        ultimo_id = ids[-1]
        status, data = mail.fetch(ultimo_id, "(RFC822)")
        
        for resposta in data:
            if isinstance(resposta, tuple):
                msg = email.message_from_bytes(resposta[1])
                
                # Extrai o conteúdo do e-mail (HTML ou Texto)
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/html":
                            html_content = part.get_payload(decode=True).decode()
                            break
                else:
                    html_content = msg.get_payload(decode=True).decode()

                # Limpeza básica com BeautifulSoup
                soup = BeautifulSoup(html_content, "html.parser")
                texto_limpo = soup.get_text(separator='\n')
                
                # Exemplo de Regex para pegar o padrão de salário que vimos no seu PDF
                # Busca "R$" seguido de números, espaços e "por mês" ou intervalos
                padrao_salario = r"R\$\s?[\d\.]+(?:\s?-\s?R\$\s?[\d\.]+)?(?:\s?por mês)?"
                salarios_encontrados = re.findall(padrao_salario, texto_limpo)
                
                print(f"Salários detectados no e-mail: {salarios_encontrados}")
                
    return lista_vagas

# Para rodar, você precisará de uma "Senha de App" do Gmail nas variáveis de ambiente do Render
# usuario = "seu_email@gmail.com"
# senha = "sua_senha_de_app"
# mail = conectar_email(usuario, senha)
# buscar_vagas_indeed(mail)