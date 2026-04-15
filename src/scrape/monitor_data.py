import os
import time
import re
import logging
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Importar o serviço de banco de dados do projeto
from src.services.database import get_sqlite_connection, get_estrutura_uid, get_default_estrutura_info

# Configuração do logger
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do Site via .env
URL_LOGIN = os.getenv("URL_LOGIN", "https://general-system.noctua-iot.com/login")
EMAIL = os.getenv("LOGIN_EMAIL")
PASSWORD = os.getenv("LOGIN_PASSWORD")
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

def get_driver():
    """Configura o driver do Chrome em modo headless com fallback de localização."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    # Lista de caminhos prováveis do ChromeDriver para diferentes distros
    possiveis_caminhos = [
        CHROMEDRIVER_PATH,
        "/usr/bin/chromedriver",
        "/usr/lib/chromium-browser/chromedriver",
        "/usr/local/bin/chromedriver"
    ]

    service = None
    for caminho in possiveis_caminhos:
        if caminho and os.path.exists(caminho):
            logger.info("Usando ChromeDriver encontrado em: %s", caminho)
            service = Service(executable_path=caminho)
            break
    
    if not service:
        logger.warning("ChromeDriver não encontrado nos caminhos padrão. Tentando via PATH do sistema")
        service = Service()
        
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        logger.error("Erro ao iniciar WebDriver: %s", e)
        raise

def scrape_and_save():
    max_tentativas = 5
    tentativa = 1
    sucesso = False

    if not EMAIL or not PASSWORD:
        logger.error("LOGIN_EMAIL ou LOGIN_PASSWORD não configurados no arquivo .env")
        return

    while tentativa <= max_tentativas and not sucesso:
        driver = None
        conn = None
        try:
            logger.info("Iniciando tentativa %d...", tentativa)

            # Garantir que a pasta do banco de dados exista (SQLITE_DB_PATH vem do database service)
            from src.services.database import SQLITE_DB_PATH
            os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)

            driver = get_driver()
            conn = get_sqlite_connection()
            if not conn:
                raise Exception("Não foi possível conectar ao banco de dados SQLite.")
            
            cursor = conn.cursor()

            # Garantir que a tabela exista antes de prosseguir (Novo MER)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS leituras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    estrutura_uid TEXT,
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
            wait = WebDriverWait(driver, 10)
            
            email_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"]')))
            driver.find_element(By.CSS_SELECTOR, 'input[type="password"]').send_keys(PASSWORD)
            email_field.send_keys(EMAIL)
            driver.find_element(By.XPATH, "//button[contains(text(), 'Entrar')]").click()

            # 2. Mapeamento de Tanques Reais (Filtro MAC Address)
            logger.info("Mapeando tanques (filtrando MACs)...")
            time.sleep(5)
            links_elementos = driver.find_elements(By.XPATH, "//a[contains(@href, '/tanque/')]")
            raw_urls = list(set([el.get_attribute('href') for el in links_elementos]))
            
            # Regex para ignorar '/MAC' e pegar apenas IDs hexadecimais
            padrao_mac = re.compile(r'/tanque/([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$')
            urls_validas = [url for url in raw_urls if padrao_mac.search(url)]

            if not urls_validas:
                # Tentar novamente se não encontrar tanques (pode ser tempo de carregamento)
                logger.warning("Nenhum tanque válido encontrado. Aguardando mais 10s...")
                time.sleep(5)
                links_elementos = driver.find_elements(By.XPATH, "//a[contains(@href, '/tanque/')]")
                raw_urls = list(set([el.get_attribute('href') for el in links_elementos]))
                urls_validas = [url for url in raw_urls if padrao_mac.search(url)]
                
                if not urls_validas:
                    raise Exception("Nenhum tanque válido encontrado no menu.")

            # 3. Coleta Individual
            for url in urls_validas:
                mac_id = url.split('/')[-1]
                logger.info("Acessando Tanque: %s", mac_id)
                driver.get(url)
                time.sleep(6) # Tempo para o React/Next.js carregar o estado

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
                        logger.warning("%s ignorado (O2/Temp em zero).", nome)
                        continue

                    # Tratamento de Timestamp
                    ts_sql = None
                    if time_match:
                        try:
                            dt_obj = datetime.strptime(time_match.group(1), '%d/%m/%Y, %H:%M:%S')
                            ts_sql = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            logger.warning("Erro ao formatar data: %s", time_match.group(1))

                    # Recupera info da estrutura do .env para bater com o nome coletado
                    info_env = get_default_estrutura_info()
                    pluscode = info_env['pluscode'] if nome == info_env['nome'] else "UNKNOWN"
                    uid = get_estrutura_uid(nome, pluscode)

                    # Gravação seguindo o Novo Schema
                    cursor.execute('''
                        INSERT INTO leituras (estrutura_uid, nome_estrutura, oxigenio, temperatura, aeradores_ativos, timestamp_site)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (uid, nome, oxigenio, temperatura, aeradores, ts_sql))
                    
                    logger.info("%s | O2: %s | Temp: %s | Aeradores: %s", nome, oxigenio, temperatura, aeradores)

            conn.commit()
            logger.info("Todos os dados salvos com sucesso!")
            sucesso = True

        except Exception as e:
            logger.error("Erro na tentativa %d: %s", tentativa, e)
            tentativa += 1
            if tentativa <= max_tentativas:
                atraso = 5 * tentativa
                logger.info("Reiniciando em %d segundos...", atraso)
                time.sleep(atraso)
        
        finally:
            if driver:
                driver.quit()
            if conn:
                conn.close()

if __name__ == "__main__":
    # Configuração básica de logging para execução direta
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    # Para executar este script manualmente do root do projeto:
    # python3 -m src.scrape.monitor_data
    scrape_and_save()
    conn.close()

if __name__ == "__main__":
    # Configuração básica de logging para execução direta
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    # Para executar este script manualmente do root do projeto:
    # python3 -m src.scrape.monitor_data
    scrape_and_save()
