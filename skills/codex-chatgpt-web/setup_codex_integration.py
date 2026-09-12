"""
setup_codex_integration.py
Configuracao manual da integracao codex-chatgpt-web com Codex CLI
Realiza o que o setup automatico faria no Windows/macOS
"""
import json
import re
import sys
from pathlib import Path

CODEX_CONFIG = Path.home() / ".codex" / "config.toml"
CGTW_CONFIG = Path.home() / ".codex-chatgpt-web" / "config.json"
CGTW_PROJECT = Path(r"C:\Users\devel\codex-chatgpt-web")
BRIDGE_PORT = 17841
BRIDGE_HOST = "127.0.0.1"

# Models disponiveis
MODELS = {
    "luna": "chatgpt-web/gpt-5.6-luna",
    "sol": "chatgpt-web/gpt-5.6-sol",
    "sol-medium": "chatgpt-web/gpt-5.6-sol:medium",
    "sol-high": "chatgpt-web/gpt-5.6-sol:high",
    "sol-xhigh": "chatgpt-web/gpt-5.6-sol:xhigh",
    "sol-ultra": "chatgpt-web/gpt-5.6-sol:ultra",
}

def load_cgtw_config() -> dict:
    """Carrega configuracao do codex-chatgpt-web."""
    if CGTW_CONFIG.exists():
        try:
            return json.loads(CGTW_CONFIG.read_text())
        except:
            pass
    return {}

def install_codex_route(config: dict) -> bool:
    """Instala a rota do Codex modificando config.toml."""
    if not CODEX_CONFIG.exists():
        print(f"[!] Config do Codex nao encontrado: {CODEX_CONFIG}")
        return False
    
    text = CODEX_CONFIG.read_text()
    route_url = f"http://{BRIDGE_HOST}:{BRIDGE_PORT}/v1"
    
    # Verifica se ja esta instalado
    if route_url in text:
        print("[+] Rota ja instalada no Codex")
        return True
    
    # Verifica se tem comment de.managed
    managed_comment = "# managed by codex-chatgpt-web"
    if managed_comment in text:
        print("[+] Rota ja estava gerenciada anteriormente")
        # Restore primeiro
        text = restore_codex_route(text)
    
    # Adiciona a rota
    # Encontra a secao [model] ou adiciona no top-level
    lines = text.split("\n")
    
    # Procura por openai_base_url existente
    found_url = False
    for i, line in enumerate(lines):
        if "openai_base_url" in line:
            lines[i] = f'openai_base_url = "{route_url}"'
            found_url = True
            break
    
    if not found_url:
        # Adiciona no inicio do arquivo (antes de qualquer [section])
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith("["):
                insert_pos = i
                break
            insert_pos = i + 1
        
        lines.insert(insert_pos, f'# {managed_comment}')
        lines.insert(insert_pos + 1, f'openai_base_url = "{route_url}"')
        lines.insert(insert_pos + 2, '')
    
    # Salva
    CODEX_CONFIG.write_text("\n".join(lines))
    print(f"[+] Rota instalada: {route_url}")
    print(f"[+] Config salvo em: {CODEX_CONFIG}")
    return True

def restore_codex_route(text: str) -> str:
    """Restaura configuracao original do Codex."""
    managed_comment = "# managed by codex-chatgpt-web"
    route_url = f"http://{BRIDGE_HOST}:{BRIDGE_PORT}/v1"
    
    lines = text.split("\n")
    new_lines = []
    skip_next = 0
    
    for i, line in enumerate(lines):
        if skip_next > 0:
            skip_next -= 1
            continue
        
        # Remove linha de comment e openai_base_url gerenciada
        if managed_comment in line:
            # Tambem remove proxima linha se for openai_base_url
            if i + 1 < len(lines) and "openai_base_url" in lines[i + 1]:
                skip_next = 1
            continue
        
        if "openai_base_url" in line and route_url in line:
            continue
        
        new_lines.append(line)
    
    return "\n".join(new_lines)

def uninstall_codex_route() -> bool:
    """Remove rota instalada."""
    if not CODEX_CONFIG.exists():
        return False
    
    text = CODEX_CONFIG.read_text()
    if "# managed by codex-chatgpt-web" not in text:
        print("[!] Rota nao encontrada no Codex")
        return False
    
    new_text = restore_codex_route(text)
    CODEX_CONFIG.write_text(new_text)
    print("[+] Rota removida do Codex")
    return True

def set_codex_model(model_key: str = "luna") -> bool:
    """Define modelo no Codex."""
    if model_key not in MODELS:
        print(f"[!] Modelo invalido: {model_key}")
        print(f"    Modelos disponiveis: {', '.join(MODELS.keys())}")
        return False
    
    model = MODELS[model_key]
    
    if not CODEX_CONFIG.exists():
        print(f"[!] Config do Codex nao encontrado: {CODEX_CONFIG}")
        return False
    
    text = CODEX_CONFIG.read_text()
    
    # Substitui modelo existente
    text = re.sub(r'model\s*=\s*"[^"]+"', f'model = "{model}"', text)
    
    # Se nao tinha modelo, adiciona
    if 'model =' not in text:
        lines = text.split("\n")
        # Encontra primeira secao
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith("["):
                insert_pos = i
                break
            insert_pos = i + 1
        lines.insert(insert_pos, f'model = "{model}"')
        text = "\n".join(lines)
    
    CODEX_CONFIG.write_text(text)
    print(f"[+] Modelo definido: {model}")
    return True

def start_bridge() -> dict:
    """Inicia o bridge em background."""
    import subprocess
    import os
    
    env = os.environ.copy()
    env["CODEX_CHATGPT_WEB_HOME"] = str(Path.home() / ".codex-chatgpt-web")
    
    proc = subprocess.Popen(
        ["bun", "run", str(CGTW_PROJECT / "src" / "cli.ts"), "serve"],
        cwd=str(CGTW_PROJECT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env
    )
    
    import time
    time.sleep(2)
    
    # Verifica se ainda esta rodando
    if proc.poll() is None:
        return {"success": True, "pid": proc.pid}
    else:
        return {"success": False, "error": "Processo caiu imediatamente"}

def stop_bridge() -> bool:
    """Para o bridge."""
    import subprocess
    
    # Tenta via CLI
    result = subprocess.run(
        ["bun", "run", str(CGTW_PROJECT / "src" / "cli.ts"), "service", "stop"],
        capture_output=True, timeout=10
    )
    
    if result.returncode != 0:
        # Mata processo bun que roda cli.ts
        subprocess.run(["taskkill", "/F", "/IM", "bun.exe"], capture_output=True)
    
    return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup manual codex-chatgpt-web")
    parser.add_argument("action", choices=[
        "install", "uninstall", "model", "start", "stop", "status"
    ], help="Acao a executar")
    parser.add_argument("--model", "-m", choices=list(MODELS.keys()), default="luna",
                        help="Modelo para usar (default: luna)")
    args = parser.parse_args()
    
    if args.action == "install":
        config = load_cgtw_config()
        if install_codex_route(config):
            print("\n[OK] Integracao instalada!")
            print("[+] Proximos passos:")
            print("    1. Make login: bun run codex-chatgpt-web/src/cli.ts login")
            print("    2. Start bridge: python setup_codex_integration.py start")
            print("    3. Select model: codex -c model=chatgpt-web/gpt-5.6-luna")
    
    elif args.action == "uninstall":
        if uninstall_codex_route():
            print("[OK] Integracao removida.")
    
    elif args.action == "model":
        if set_codex_model(args.model):
            print(f"[OK] Modelo alterado para: {MODELS[args.model]}")
    
    elif args.action == "start":
        result = start_bridge()
        if result["success"]:
            print(f"[OK] Bridge iniciada (PID: {result['pid']})")
            print(f"[+] Access: http://{BRIDGE_HOST}:{BRIDGE_PORT}/v1")
        else:
            print(f"[!] Falha ao iniciar: {result.get('error')}")
    
    elif args.action == "stop":
        stop_bridge()
        print("[OK] Bridge parada.")
    
    elif args.action == "status":
        import urllib.request
        try:
            req = urllib.request.Request(f"http://{BRIDGE_HOST}:{BRIDGE_PORT}/health")
            with urllib.request.urlopen(req, timeout=2) as resp:
                bridge_up = resp.status == 200
        except:
            bridge_up = False
        
        config = load_cgtw_config()
        route_installed = str(BRIDGE_PORT) in CODEX_CONFIG.read_text() if CODEX_CONFIG.exists() else False
        
        print(f"Bridge: {'UP' if bridge_up else 'DOWN'} (:{BRIDGE_PORT})")
        print(f"Route:  {'INSTALLED' if route_installed else 'NOT INSTALLED'}")
        print(f"Config: {'OK' if config else 'MISSING'}")

if __name__ == "__main__":
    main()
