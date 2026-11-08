"""Autenticacao inicial do Kommo (OAuth2).

Uso:
    uv run python auth.py "CODIGO_DE_AUTORIZACAO"

O codigo de autorizacao e gerado na tela da integracao no Kommo
(aba "Chaves e escopos" -> botao de copiar codigo). Ele dura ~20 min,
entao rode este script logo apos copiar.

Antes de rodar, preencha config.json com subdomain, client_id,
client_secret e redirect_uri (copie de config.example.json).
"""

import json
import sys
import time
from pathlib import Path

import httpx

CONFIG_PATH = Path(__file__).parent / "config.json"


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: uv run python auth.py \"CODIGO_DE_AUTORIZACAO\"")
        sys.exit(1)

    code = sys.argv[1].strip()
    if not CONFIG_PATH.exists():
        print(f"Crie {CONFIG_PATH} a partir de config.example.json primeiro.")
        sys.exit(1)

    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    for field in ("subdomain", "client_id", "client_secret"):
        if not cfg.get(field):
            print(f"Campo '{field}' vazio no config.json. Preencha antes de continuar.")
            sys.exit(1)

    url = f"https://{cfg['subdomain']}.kommo.com/oauth2/access_token"
    resp = httpx.post(
        url,
        json={
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": cfg.get("redirect_uri", "https://localhost"),
        },
        timeout=30,
    )

    if resp.status_code != 200:
        print(f"Falha ({resp.status_code}): {resp.text}")
        sys.exit(1)

    data = resp.json()
    cfg["access_token"] = data["access_token"]
    cfg["refresh_token"] = data["refresh_token"]
    cfg["expires_at"] = int(time.time()) + int(data.get("expires_in", 86400)) - 120
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Autenticado com sucesso. Tokens salvos em config.json.")
    print(f"access_token expira em ~{int(data.get('expires_in', 86400)) // 3600}h "
          "(renovado automaticamente pelo servidor).")


if __name__ == "__main__":
    main()
