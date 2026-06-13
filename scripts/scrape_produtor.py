#!/usr/bin/env python3
import os
import sys
import time
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Adiciona a raiz do projeto ao path para importar monitor_data
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scrape.monitor_data import get_driver, URL_LOGIN, EMAIL, PASSWORD

def main():
    load_dotenv()
    print("--- Scraping de Produtor ---")
    print(f"URL Login: {URL_LOGIN}")
    print(f"E-mail: {EMAIL}")
    
    driver = None
    try:
        driver = get_driver()
        print("Iniciando login no site...")
        driver.get(URL_LOGIN)
        
        # Espera carregar os campos e realiza o login
        time.sleep(3)
        email_field = driver.find_element(by="css selector", value='input[type="email"]')
        pass_field = driver.find_element(by="css selector", value='input[type="password"]')
        
        pass_field.send_keys(PASSWORD)
        email_field.send_keys(EMAIL)
        
        # Clica em entrar
        login_btn = driver.find_element(by="xpath", value="//button[contains(text(), 'Entrar')]")
        login_btn.click()
        print("Login efetuado. Aguardando 8 segundos para redirecionamento...")
        time.sleep(8)
        
        # Navega para a página do produtor
        target_url = "https://general-system.noctua-iot.com/produtor"
        print(f"Navegando para: {target_url}")
        driver.get(target_url)
        print("Aguardando carregamento da página do produtor...")
        time.sleep(8)
        
        # Captura o HTML
        html = driver.page_source
        
        # Garante que a pasta logs exista
        os.makedirs("logs", exist_ok=True)
        # Salva o HTML temporário local para fins de depuração se necessário
        with open("logs/produtor_page.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        print("HTML capturado e salvo em logs/produtor_page.html.")
        
        # Análise com BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. Título da página ou cabeçalhos
        print("\n--- Cabeçalhos Encontrados (H1, H2, H3) ---")
        for h in soup.find_all(['h1', 'h2', 'h3']):
            print(f"- {h.name}: {h.get_text(strip=True)}")
            
        # 2. Tabelas
        print("\n--- Tabelas Encontradas ---")
        tables = soup.find_all('table')
        print(f"Total de tabelas: {len(tables)}")
        for idx, table in enumerate(tables):
            print(f"\nTabela {idx+1}:")
            # Cabeçalhos
            headers = [th.get_text(strip=True) for th in table.find_all('th')]
            if headers:
                print(" | ".join(headers))
            # Linhas
            for row in table.find_all('tr'):
                cols = [td.get_text(strip=True) for td in row.find_all('td')]
                if cols:
                    print(" | ".join(cols))
                    
        # 3. Listas ou Cards (divs com texto que parecem conter dados do produtor)
        print("\n--- Informações de Blocos/Cards de Dados ---")
        text_content = soup.get_text(separator='\n')
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        
        # Filtra linhas interessantes
        palavras_chave = ['produtor', 'propriedade', 'cnpj', 'cpf', 'cadpro', 'silo', 'ração', 'lote', 'entrega', 'peixe', 'endereço', 'fone', 'telefone']
        encontrados = False
        for line in lines:
            for kw in palavras_chave:
                if kw in line.lower():
                    print(f"  > {line}")
                    encontrados = True
                    break
        if not encontrados:
            print("Nenhuma palavra-chave de dados de produtor encontrada no texto direto.")
            # Imprime as primeiras 50 linhas do texto para termos contexto
            print("\nPrimeiras 50 linhas de texto da página:")
            for line in lines[:50]:
                print(f"  {line}")
                
    except Exception as e:
        print(f"Erro ao capturar dados de produtor: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
