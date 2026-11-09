"""Grava um token de longa duracao do Kommo no config.json.

E o jeito mais simples de ligar o Claude ao Kommo: o token e gerado na
propria integracao (aba "Chaves e escopos" -> gerar token de longa
duracao), vale ate a data escolhida na hora de gerar e dispensa o
auth.py e o refresh_token.

Uso:
    uv run python token_longo.py

O script pede o subdominio (se ainda nao estiver no config.json) e o
token, sem mostrar o token na tela. Depois testa a conexao.
"""

from __future__ import annotations

import base64
import getpass
import json
import sys
import time
from datetime import datetime
from pathlib import Path

PASTA = Path(__file__).parent
CONFIG_PATH = PASTA / "config.json"
EXAMPLE_PATH = PASTA / "config.example.json"
PLACEHOLDER = "suaempresa"


def _validade(token: str) -> int | None:
    """Le a data de expiracao (campo exp) de dentro do token."""
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return int(json.loads(base64.urlsafe_b64decode(payload))["exp"])
    except Exception:
        return None


def _limpar_subdominio(texto: str) -> str:
    texto = texto.strip().replace("https://", "").replace("http://", "")
    return texto.split(".kommo.com")[0].strip("/ ")


def main() -> None:
    origem = CONFIG_PATH if CONFIG_PATH.exists() else EXAMPLE_PATH
    cfg = json.loads(origem.read_text(encoding="utf-8"))

    sub = _limpar_subdominio(cfg.get("subdomain", ""))
    if not sub or sub == PLACEHOLDER:
        sub = _limpar_subdominio(
            input("Subdominio da conta (o 'suaempresa' de suaempresa.kommo.com): ")
        )
    if not sub:
        print("Sem subdominio nao da para continuar.")
        sys.exit(1)

    token = getpass.getpass(
        "Cole o token de longa duracao (ele nao aparece na tela) e tecle Enter: "
    ).strip()
    if token.count(".") != 2:
        print("Isso nao parece um token do Kommo (esperava tres partes separadas por ponto).")
        sys.exit(1)

    exp = _validade(token)
    if exp is None:
        print("Nao consegui ler a validade do token. Confira se copiou o token inteiro.")
        sys.exit(1)
    if exp <= time.time():
        print("Esse token ja venceu. Gere outro na integracao do Kommo.")
        sys.exit(1)

    cfg.update(
        {
            "subdomain": sub,
            "access_token": token,
            "refresh_token": "",
            "expires_at": exp - 120,
            "long_lived": True,
        }
    )
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        CONFIG_PATH.chmod(0o600)  # so o seu usuario le o arquivo
    except OSError:
        pass
    print(f"Token salvo em {CONFIG_PATH.name}. Vale ate {datetime.fromtimestamp(exp):%d/%m/%Y}.")

    try:
        import kommo_client as kc

        conta = kc.request("GET", "/account")
        print(f"Conexao OK: conta \"{conta.get('name')}\" ({sub}.kommo.com).")
    except Exception as erro:  # noqa: BLE001
        print(f"O token foi salvo, mas o teste falhou: {erro}")
        sys.exit(1)


if __name__ == "__main__":
    main()
