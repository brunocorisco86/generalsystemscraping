#!/usr/bin/env python3
"""Descobre dinamicamente os dados de integração do painel Noctua IoT.

Requisitos:
    pip install playwright
    playwright install chromium

Uso:
    python scripts/noctua_diagnose.py --env .env
    python scripts/noctua_diagnose.py --env .env --no-write
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Instale a dependência com: pip install playwright && playwright install chromium") from exc


MAC_RE = re.compile(r"(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}")
APPSYNC_RE = re.compile(r"https://[^\"'\s]+\.appsync-api\.[^\"'\s]+/graphql")


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def update_env(path: Path, updates: dict[str, str]) -> None:
    original = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = original.splitlines()
    output: list[str] = []
    written: set[str] = set()

    for line in lines:
        match = re.match(r"^(\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*=).*$", line)
        if match and match.group(2) in updates:
            key = match.group(2)
            output.append(f"{key}={updates[key]}")
            written.add(key)
        else:
            output.append(line)

    missing = [key for key in updates if key not in written]
    if missing:
        if output and output[-1] != "":
            output.append("")
        output.append("# --- Descoberto dinamicamente via scripts/noctua_diagnose.py ---")
        output.extend(f"{key}={updates[key]}" for key in missing)
    path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")


def unique(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        value = value.strip()
        if value and value not in result:
            result.append(value)
    return result


def extract_macs(values: list[str]) -> list[str]:
    found: list[str] = []
    for value in values:
        for mac in MAC_RE.findall(value or ""):
            mac = mac.upper()
            if mac not in found:
                found.append(mac)
    return found


def extract_graphql_urls(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        for url in APPSYNC_RE.findall(value or ""):
            if url not in result:
                result.append(url)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", default=".env", help="Arquivo .env")
    parser.add_argument("--email", help="Email de login (sobrescreve .env)")
    parser.add_argument("--password", help="Senha de login (sobrescreve .env)")
    parser.add_argument("--no-write", action="store_true", help="Somente diagnosticar")
    parser.add_argument("--headful", action="store_true", help="Exibir o navegador durante a execução")
    args = parser.parse_args()

    env_path = Path(args.env).expanduser().resolve()
    env = read_env(env_path)

    base_url = (env.get("NOCTUA_BASE_URL") or "https://general-system.noctua-iot.com").rstrip("/")
    email = args.email or env.get("NOCTUA_EMAIL") or env.get("LOGIN_EMAIL", "")
    password = args.password or env.get("NOCTUA_PASSWORD") or env.get("LOGIN_PASSWORD", "")

    if not email or not password:
        print("ERRO: informe NOCTUA_EMAIL e NOCTUA_PASSWORD no .env ou via parâmetros --email/--password.", file=sys.stderr)
        return 2

    graphql_urls: list[str] = []
    graphql_keys: list[str] = []
    request_urls: list[str] = []
    diagnosis: dict[str, Any] = {
        "diagnosed_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "http_status": {},
        "graphql_urls_seen": [],
        "request_count": 0,
    }

    print(f"Iniciando diagnóstico via Playwright em {base_url}...")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=not args.headful,
            proxy={"server": "direct://"},
            args=["--proxy-server=direct://", "--no-proxy-server", "--disable-gpu"]
        )
        context = browser.new_context()
        page = context.new_page()

        def capture_request(request: Any) -> None:
            url = request.url
            request_urls.append(url)
            if ".appsync-api." in url and url.endswith("/graphql"):
                graphql_urls.append(url)
                headers = request.all_headers()
                key = headers.get("x-api-key") or headers.get("X-Api-Key")
                if key:
                    graphql_keys.append(key)

        page.on("request", capture_request)
        page.on("response", lambda response: diagnosis["http_status"].update({response.url: response.status}) if "/api/auth/" in response.url else None)

        try:
            print("Navegando para tela de login...")
            page.goto(f"{base_url}/login", wait_until="domcontentloaded", timeout=60000)
            page.locator('input[type="email"]').fill(email)
            page.locator('input[type="password"]').fill(password)
            page.get_by_role("button", name=re.compile("Entrar", re.I)).click()
            print("Autenticação enviada, aguardando carregamento e rede...")
            page.wait_for_timeout(5000)
            page.wait_for_load_state("networkidle", timeout=30000)
        except PlaywrightTimeoutError:
            page.wait_for_timeout(3000)
        except Exception as exc:
            browser.close()
            print(f"ERRO ao autenticar: {exc}", file=sys.stderr)
            return 1

        diagnosis["final_url"] = page.url
        diagnosis["page_title"] = page.title()
        diagnosis["request_count"] = len(request_urls)

        # Tempo para o dashboard executar queries iniciais
        page.wait_for_timeout(4000)
        storage = page.evaluate(
            """() => ({
                localStorage: Object.fromEntries(Object.entries(localStorage)),
                sessionStorage: Object.fromEntries(Object.entries(sessionStorage)),
                hrefs: Array.from(document.querySelectorAll('a')).map(a => a.href),
                html: document.documentElement.outerHTML
            })"""
        )
        cookies = context.cookies()
        browser.close()

    session_storage = storage.get("sessionStorage", {})
    local_storage = storage.get("localStorage", {})
    html = storage.get("html", "")
    hrefs = storage.get("hrefs", [])

    text_sources = [html, json.dumps(hrefs), json.dumps(session_storage), json.dumps(local_storage)]
    graphql_urls = unique(graphql_urls + extract_graphql_urls(text_sources))
    graphql_keys = unique(graphql_keys)

    endpoints: list[dict[str, Any]] = []
    for key in ("endpoints", "latestSensorData"):
        raw = session_storage.get(key)
        if not raw:
            continue
        try:
            decoded = json.loads(raw)
            if isinstance(decoded, list):
                for item in decoded:
                    if isinstance(item, dict) and item not in endpoints:
                        endpoints.append(item)
        except (TypeError, json.JSONDecodeError):
            pass

    endpoint_ids = extract_macs([json.dumps(endpoints), html, json.dumps(local_storage)])
    gateway_ids = extract_macs([session_storage.get("gatewayIds", ""), json.dumps(endpoints), json.dumps(session_storage)])
    gateway_id = gateway_ids[0] if gateway_ids else ""

    diagnosis.update({
        "graphql_urls_seen": graphql_urls,
        "graphql_api_key_found": bool(graphql_keys),
        "endpoint_ids": endpoint_ids,
        "gateway_ids": gateway_ids,
        "endpoints": endpoints,
        "session_storage_keys": sorted(session_storage.keys()),
    })

    updates: dict[str, str] = {
        "NOCTUA_BASE_URL": base_url,
        "NOCTUA_EMAIL": email,
        "NOCTUA_PASSWORD": password,
    }

    if graphql_urls:
        updates["NOCTUA_APPSYNC_URL"] = graphql_urls[0]
        updates["NOCTUA_GRAPHQL_URL"] = graphql_urls[0]

    if graphql_keys:
        updates["NOCTUA_API_KEY"] = graphql_keys[0]
        updates["NOCTUA_APPSYNC_API_KEY"] = graphql_keys[0]

    if gateway_id:
        updates["NOCTUA_GATEWAY_ID"] = gateway_id

    # Ordenar ou atribuir tanques
    for idx, ep_mac in enumerate(endpoint_ids[:2], start=1):
        updates[f"NOCTUA_ENDPOINT_TANQUE_{idx}"] = ep_mac

    report_json = json.dumps(diagnosis, ensure_ascii=False, indent=2)
    if args.no_write:
        print("\n--- Relatório de Diagnóstico ---")
        print(report_json)
    else:
        update_env(env_path, updates)
        report_path = env_path.with_name("noctua_diagnosis.json")
        report_path.write_text(report_json + "\n", encoding="utf-8")
        print(f"\n✅ Diagnóstico concluído com sucesso!")
        print(f"Arquivo de relatório: {report_path}")
        print(f"Arquivo .env atualizado: {env_path}")
        print(f"GraphQL URL: {graphql_urls[0] if graphql_urls else 'Não encontrada'}")
        print(f"Chave API Key capturada: {'Sim (' + graphql_keys[0][:6] + '...)' if graphql_keys else 'Não'}")
        print(f"Gateway ID: {gateway_id}")
        print(f"Endpoints encontrados: {endpoint_ids}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
