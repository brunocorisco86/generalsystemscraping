#!/usr/bin/env python3
"""
scripts/15-auto-configure-macs.py: Automação de comissionamento de MACs.
Faz login no Noctua-IoT, extrai os MACs dos tanques e atualiza a variável
STRUCT_MACS diretamente no arquivo .env do projeto.
"""
import os
import sys
import time
import re
from pathlib import Path
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Adiciona a raiz do projeto ao path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.scrape.monitor_data import get_driver, URL_LOGIN, EMAIL, PASSWORD

def update_env_file(mac_string: str):
    """Atualiza ou insere a variável STRUCT_MACS no arquivo .env."""
    env_path = project_root / ".env"
    if not env_path.exists():
        print(f"ERRO: Arquivo .env não encontrado em {env_path}")
        return False
        
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    replaced = False
    new_lines = []
    for line in lines:
        if line.strip().startswith("STRUCT_MACS="):
            new_lines.append(f'STRUCT_MACS="{mac_string}"\n')
            replaced = True
        else:
            new_lines.append(line)
            
    if not replaced:
        new_lines.append(f'\n# Adicionado automaticamente pelo configurador de MACs:\nSTRUCT_MACS="{mac_string}"\n')
        
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
        
    print(f"✅ Arquivo .env atualizado com sucesso com STRUCT_MACS!")
    return True

def main():
    load_dotenv(project_root / ".env")
    print("--- [15] Automação de Comissionamento de MAC Addresses ---")
    
    if not EMAIL or not PASSWORD:
        print("ERRO: LOGIN_EMAIL ou LOGIN_PASSWORD não configurados no arquivo .env.")
        print("Por favor, preencha essas credenciais no seu arquivo .env antes de rodar este script.")
        sys.exit(1)
        
    print(f"Tentando login para o e-mail: {EMAIL}")
    driver = None
    try:
        driver = get_driver()
        driver.get(URL_LOGIN)
        
        # Espera carregar os campos e realiza o login
        time.sleep(3)
        email_field = driver.find_element(by="css selector", value='input[type="email"]')
        pass_field = driver.find_element(by="css selector", value='input[type="password"]')
        
        pass_field.send_keys(PASSWORD)
        email_field.send_keys(EMAIL)
        
        login_btn = driver.find_element(by="xpath", value="//button[contains(text(), 'Entrar')]")
        login_btn.click()
        print("Login efetuado. Aguardando redirecionamento...")
        time.sleep(8)
        
        print("Acessando página /produtor...")
        driver.get("https://general-system.noctua-iot.com/produtor")
        time.sleep(6)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Extrai os tanques e seus MACs
        tanques_site = []
        for p_el in soup.find_all(string=re.compile(r'MAC:\s*[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}')):
            mac_match = re.search(r'([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}', p_el)
            if mac_match:
                mac_addr = mac_match.group(0)
                parent = p_el.parent
                name = "Desconhecido"
                if parent:
                    sibling = parent.find_previous_sibling() or parent.parent.find('p', class_='text-gray-800')
                    if sibling:
                        name = sibling.get_text(strip=True)
                    else:
                        parent_text = parent.parent.get_text()
                        name_match = re.search(r'(Tanque\s*\d+)', parent_text)
                        if name_match:
                            name = name_match.group(1)
                
                name_upper = name.strip().upper() if name else ""
                if name_upper and "TANQUE" in name_upper and "N/A" not in name_upper and "DESCONHECIDO" not in name_upper:
                    tanques_site.append((name.strip(), mac_addr))
                    
        # Remove duplicados
        seen = set()
        tanques_unicos = []
        for name, mac in tanques_site:
            if mac not in seen:
                seen.add(mac)
                tanques_unicos.append((name, mac))
                
        if not tanques_unicos:
            print("❌ Nenhum tanque encontrado na página do produtor do site.")
            sys.exit(1)
            
        print(f"Encontrados {len(tanques_unicos)} tanques no site:")
        macs_list = []
        for name, mac in tanques_unicos:
            print(f"  - {name}: {mac}")
            macs_list.append(f"{name}:{mac}")
            
        # Constrói a string do STRUCT_MACS
        mac_string = ", ".join(macs_list)
        print(f"String gerada: STRUCT_MACS=\"{mac_string}\"")
        
        # Atualiza o arquivo .env
        update_env_file(mac_string)
        
    except Exception as e:
        print(f"❌ Erro ao comissionar MACs: {e}")
        sys.exit(1)
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
