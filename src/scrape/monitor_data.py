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
from bs4 import BeautifulSoup

# Importar o serviço de banco de dados do projeto
from src.services.database import (
    get_sqlite_connection, 
    get_estrutura_uid, 
    get_default_estrutura_info,
    get_all_estruturas_map
)

# Configuração do logger
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do Site via .env
URL_LOGIN = os.getenv("URL_LOGIN", "https://general-system.noctua-iot.com/login")
EMAIL = os.getenv("LOGIN_EMAIL")
PASSWORD = os.getenv("LOGIN_PASSWORD")
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
STRUCT_MACS_RAW = os.getenv("STRUCT_MACS", "")

def get_configured_macs() -> dict:
    """Carrega os MACs configurados localmente no .env no formato Nome:MAC."""
    macs = {}
    if STRUCT_MACS_RAW:
        parts = STRUCT_MACS_RAW.split(',')
        for p in parts:
            if ':' in p:
                name, mac = p.strip().split(':', 1)
                macs[name.strip()] = mac.strip()
    return macs

def get_driver():
    """Configura o driver do Chrome em modo headless com fallback de localização e otimizações de RAM."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    # Otimizações de baixo consumo de RAM para hardware limitado (ex: Raspberry Pi)
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--no-zygote")
    chrome_options.add_argument("--disable-gpu-program-cache")
    chrome_options.add_argument("--disable-gpu-shader-disk-cache")
    
    # Desativa o carregamento de imagens para poupar memória e banda
    chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    
    # Estratégia de carregamento Eager: retorna assim que o HTML/DOM básico carregar, sem esperar mídias
    chrome_options.page_load_strategy = 'eager'

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

            # Mapa de Estruturas para resolver UIDs
            estruturas_map = get_all_estruturas_map()
            if not estruturas_map:
                logger.warning("Nenhuma estrutura cadastrada no banco. UIDs podem ser gerados incorretamente.")

            # Garantir que a tabela exista antes de prosseguir (Novo MER)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS leituras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    estrutura_uid TEXT,
                    nome_estrutura TEXT,
                    oxigenio REAL,
                    temperatura REAL,
                    timestamp_site TIMESTAMP,
                    data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    aeradores_ativos INTEGER DEFAULT 0
                )
            ''')
            
            # Migração: Garante que a coluna nome_estrutura exista em bancos antigos
            try:
                cursor.execute("ALTER TABLE leituras ADD COLUMN nome_estrutura TEXT")
            except:
                pass

            conn.commit()

            # 1. Login
            driver.get(URL_LOGIN)
            wait = WebDriverWait(driver, 10)
            
            email_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"]')))
            driver.find_element(By.CSS_SELECTOR, 'input[type="password"]').send_keys(PASSWORD)
            email_field.send_keys(EMAIL)
            driver.find_element(By.XPATH, "//button[contains(text(), 'Entrar')]").click()

            # 2. Auditoria e Conferência de MAC Addresses (/produtor)
            logger.info("Aguardando login concluir e redirecionar...")
            time.sleep(5)
            
            local_macs = get_configured_macs()
            urls_validas = []
            tanques_site_unicos = []
            
            try:
                # Navega para a página de perfil para auditar e extrair os MACs ativos
                logger.info("Acessando página /produtor para realizar a conferência de MACs...")
                driver.get("https://general-system.noctua-iot.com/produtor")
                time.sleep(6) # Tempo para renderização dinâmica
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Procura por MAC addresses no texto da página
                tanques_site = []
                for p_el in soup.find_all(string=re.compile(r'MAC:\s*[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}')):
                    mac_match = re.search(r'([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}', p_el)
                    if mac_match:
                        mac_addr = mac_match.group(0)
                        
                        # Tenta encontrar o nome do tanque correspondente
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
                        
                        # Filtra apenas o que parece ser Tanque (exclui o Gateway e nomes inválidos como N/A)
                        name_upper = name.strip().upper() if name else ""
                        if name_upper and "TANQUE" in name_upper and "N/A" not in name_upper and "DESCONHECIDO" not in name_upper:
                            tanques_site.append((name.strip(), mac_addr))
                
                # Remove duplicados
                seen_macs = set()
                for name, mac_addr in tanques_site:
                    if mac_addr not in seen_macs:
                        seen_macs.add(mac_addr)
                        tanques_site_unicos.append((name, mac_addr))
                
                # Executa a conferência comparando com as configurações locais
                logger.info("--- [Relatório de Conferência de MAC Addresses] ---")
                local_mac_vals = list(local_macs.values())
                
                for name, mac_addr in tanques_site_unicos:
                    if mac_addr not in local_mac_vals:
                        logger.warning("[CONFERENCIA] Novo tanque detectado no site mas ausente no .env: %s (MAC: %s)", name, mac_addr)
                    else:
                        logger.info("[CONFERENCIA] Tanque validado: %s (MAC: %s)", name, mac_addr)
                    urls_validas.append(f"https://general-system.noctua-iot.com/tanque/{mac_addr}")
                
                # Avisa caso tanques do .env não estejam no site
                site_mac_vals = [m for _, m in tanques_site_unicos]
                for name, mac_addr in local_macs.items():
                    if mac_addr not in site_mac_vals:
                        logger.warning("[CONFERENCIA] Tanque configurado localmente (%s, MAC: %s) não foi exibido na página do site!", name, mac_addr)
                        urls_validas.append(f"https://general-system.noctua-iot.com/tanque/{mac_addr}")
                
                if not urls_validas:
                    logger.warning("Nenhum tanque listado no site. Usando fallbacks do .env...")
                    for mac_addr in local_macs.values():
                        urls_validas.append(f"https://general-system.noctua-iot.com/tanque/{mac_addr}")
                        
            except Exception as audit_err:
                logger.error("Erro na rotina de conferência de MACs: %s. Utilizando chaves locais como fallback...", audit_err)
                for mac_addr in local_macs.values():
                    urls_validas.append(f"https://general-system.noctua-iot.com/tanque/{mac_addr}")
            
            # Garante que não temos duplicatas de URLs
            urls_validas = list(dict.fromkeys(urls_validas))
            
            if not urls_validas:
                raise Exception("Nenhum endereço de tanque disponível para scraping.")
            
            logger.info("Mapeamento concluído com sucesso. URLs a serem monitoradas diretamente: %s", urls_validas)

            # Construir mapa de MAC para Nome para resolução estática
            mac_to_name = {}
            for name, mac in local_macs.items():
                mac_to_name[mac.strip().lower()] = name.strip()
            for name, mac in tanques_site_unicos:
                mac_to_name[mac.strip().lower()] = name.strip()

            # 3. Coleta Individual
            for url in urls_validas:
                mac_id = url.split('/')[-1].strip().lower()
                
                # Tenta recuperar o nome pelo MAC id
                nome = mac_to_name.get(mac_id)
                if not nome:
                    for m_key, n_val in mac_to_name.items():
                        if m_key.lower() == mac_id:
                            nome = n_val
                            break
                if not nome:
                    nome = f"Tanque {mac_id.upper()}"

                logger.info("Acessando Tanque: %s (MAC: %s)", nome, mac_id)
                driver.get(url)
                time.sleep(12) # Tempo conservador para o React/Next.js carregar o estado dos sensores

                # JS Cirúrgico para extrair Texto e Aeradores
                js_extrair = r'''
                let motoresLabel = Array.from(document.querySelectorAll('div')).find(el => el.innerText === 'Motores');
                let bolinhas = 0;
                if (motoresLabel) {
                    let box = motoresLabel.parentElement;
                    bolinhas = box.querySelectorAll('div.bg-green-500').length;
                }
                return {
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

                    # Recupera o UID correto do mapa (ou gera um fallback se não existir)
                    uid = estruturas_map.get(nome)
                    if not uid:
                        logger.warning("UID para %s não encontrado no mapa. Gerando fallback...", nome)
                        info_env = get_default_estrutura_info()
                        pluscode = info_env['pluscode'] if nome == info_env['nome'] else "UNKNOWN"
                        uid = get_estrutura_uid(nome, pluscode)

                    nome_upper = nome.strip().upper() if nome else ""
                    if not nome_upper or "N/A" in nome_upper or "DESCONHECIDO" in nome_upper:
                        logger.warning("Ignorando inserção de leitura para tanque com nome inválido/N/A: %s", nome)
                        continue

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
    scrape_and_save()
