import os
import time
import re
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Importar o serviço de banco de dados do projeto
from src.services.database import get_sqlite_connection

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do Site via .env
URL_LOGIN = os.getenv("URL_LOGIN", "https://general-system.noctua-iot.com/login")
EMAIL = os.getenv("LOGIN_EMAIL")
PASSWORD = os.getenv("LOGIN_PASSWORD")
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

def get_driver():
    """Configura o driver do Chrome em modo headless com flags de estabilidade."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") # Nova versão do headless mais estável
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    # Verifica se o chromedriver existe no caminho especificado
    if not os.path.exists(CHROMEDRIVER_PATH):
        # Tentar encontrar no PATH se não estiver no caminho fixo
        service = Service()
    else:
        service = Service(executable_path=CHROMEDRIVER_PATH)
        
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scrape_and_save():
    max_tentativas = 3
    tentativa = 1
    sucesso = False

    if not EMAIL or not PASSWORD:
        print("❌ LOGIN_EMAIL ou LOGIN_PASSWORD não configurados no arquivo .env")
        return

    while tentativa <= max_tentativas and not sucesso:
        driver = None
        conn = None
        try:
            print(f"[{datetime.now()}] Iniciando tentativa {tentativa}...")

            # Garantir que a pasta do banco de dados exista (SQLITE_DB_PATH vem do database service)
            from src.services.database import SQLITE_DB_PATH
            os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)

            driver = get_driver()
            conn = get_sqlite_connection()
            if not conn:
                raise Exception("Não foi possível conectar ao banco de dados SQLite.")
            
            cursor = conn.cursor()

            # Garantir que a tabela exista antes de prosseguir
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS leituras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tanque TEXT,
                    oxigenio REAL,
                    temperatura REAL,
                    timestamp_site TIMESTAMP,
                    data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    aeradores_ativos INTEGER DEFAULT 0
                )
            ''')
            conn.commit()

            # 1. Login
            driver.get(URL_LOGIN)
            wait = WebDriverWait(driver, 30)
            
            email_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"]')))
            driver.find_element(By.CSS_SELECTOR, 'input[type="password"]').send_keys(PASSWORD)
            email_field.send_keys(EMAIL)
            driver.find_element(By.XPATH, "//button[contains(text(), 'Entrar')]").click()

            # 2. Mapeamento de Tanques Reais (Filtro MAC Address)
            print("Mapeando tanques (filtrando MACs)...")
            time.sleep(10)
            links_elementos = driver.find_elements(By.XPATH, "//a[contains(@href, '/tanque/')]")
            raw_urls = list(set([el.get_attribute('href') for el in links_elementos]))
            
            # Regex para ignorar '/MAC' e pegar apenas IDs hexadecimais
            padrao_mac = re.compile(r'/tanque/([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$')
            urls_validas = [url for url in raw_urls if padrao_mac.search(url)]

            if not urls_validas:
                # Tentar novamente se não encontrar tanques (pode ser tempo de carregamento)
                print("⚠️ Nenhum tanque válido encontrado. Aguardando mais 10s...")
                time.sleep(10)
                links_elementos = driver.find_elements(By.XPATH, "//a[contains(@href, '/tanque/')]")
                raw_urls = list(set([el.get_attribute('href') for el in links_elementos]))
                urls_validas = [url for url in raw_urls if padrao_mac.search(url)]
                
                if not urls_validas:
                    raise Exception("Nenhum tanque válido encontrado no menu.")

            # 3. Coleta Individual
            for url in urls_validas:
                mac_id = url.split('/')[-1]
                print(f"--- Acessando Tanque: {mac_id} ---")
                driver.get(url)
                time.sleep(12) # Tempo para o React/Next.js carregar o estado

                # JS Cirúrgico para extrair Nome, Texto e Aeradores
                js_extrair = r'''
                let nomeTxt = document.body.innerText.match(/Tanque \d+/) ? document.body.innerText.match(/Tanque \d+/)[0] : "N/A";
                let motoresLabel = Array.from(document.querySelectorAll('div')).find(el => el.innerText === 'Motores');
                let bolinhas = 0;
                if (motoresLabel) {
                    let box = motoresLabel.parentElement;
                    bolinhas = box.querySelectorAll('div.bg-green-500').length;
                }
                return {
                    nome: nomeTxt,
                    corpo: document.body.innerText,
                    aeradores: Math.min(bolinhas, 5)
                };
                '''
                dados_site = driver.execute_script(js_extrair)
                full_text = dados_site['corpo']

                # Extração via Regex Python
                ox_match = re.search(r'Oxigênio.*?([\d.]+)', full_text, re.DOTALL)
                temp_match = re.search(r'Temperatura.*?([\d.]+)', full_text, re.DOTALL)
                time_match = re.search(r'(\d{2}/\d{2}/\d{4}, \d{2}:\d{2}:\d{2})', full_text)

                if ox_match and temp_match:
                    nome = dados_site['nome']
                    oxigenio = float(ox_match.group(1))
                    temperatura = float(temp_match.group(1))
                    aeradores = dados_site['aeradores']
                    
                    # Filtro de erro (sensor offline)
                    if oxigenio == 0.0 and temperatura == 0.0:
                        print(f" ⚠️ {nome} ignorado (O2/Temp em zero).")
                        continue

                    # Tratamento de Timestamp
                    ts_sql = None
                    if time_match:
                        try:
                            dt_obj = datetime.strptime(time_match.group(1), '%d/%m/%Y, %H:%M:%S')
                            ts_sql = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            print(f"  ⚠️ Erro ao formatar data: {time_match.group(1)}")

                    # Gravação seguindo o Schema solicitado
                    cursor.execute('''
                        INSERT INTO leituras (tanque, oxigenio, temperatura, aeradores_ativos, timestamp_site)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (nome, oxigenio, temperatura, aeradores, ts_sql))
                    
                    print(f"  ✅ {nome} | O2: {oxigenio} | Temp: {temperatura} | Aeradores: {aeradores}")

            conn.commit()
            print(f"[{datetime.now()}] Todos os dados salvos com sucesso!")
            sucesso = True

        except Exception as e:
            print(f"❌ Erro na tentativa {tentativa}: {e}")
            tentativa += 1
            if tentativa <= max_tentativas:
                atraso = 15 * tentativa
                print(f"Reiniciando em {atraso} segundos...")
                time.sleep(atraso)
        
        finally:
            if driver: driver.quit()
            if conn: conn.close()

if __name__ == "__main__":
    # Para executar este script manualmente do root do projeto:
    # python3 -m src.scrape.monitor_data
    scrape_and_save()
