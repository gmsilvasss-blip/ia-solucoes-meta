# Busca ampliada para pegar mais e-mails e diagnosticar
        status, mensagens = mail.search(None, '(FROM "donotreply@match.indeed.com")')
        ids = mensagens[0].split()

        if not ids:
            print("❌ DEBUG: Nenhum e-mail encontrado para o remetente Indeed.")
            return []

        print(f"✅ DEBUG: Encontrados {len(ids)} e-mails do Indeed. Analisando os 5 últimos...")
        
        vagas_encontradas = []

        # Analisamos os últimos 5 e-mails para garantir o teste
        for e_id in ids[-5:]:
            _, data = mail.fetch(e_id, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            
            # ... resto do código de extração de HTML ...
            
            soup = BeautifulSoup(corpo_html, "html.parser")
            print(f"🔎 DEBUG: Escaneando e-mail ID {e_id.decode()}...")
            
            # Aqui garantimos que o print apareça mesmo se o filtro falhar
            links = soup.find_all('a', href=True)
            print(f"🔎 DEBUG: Encontrados {len(links)} links no corpo do e-mail.")
