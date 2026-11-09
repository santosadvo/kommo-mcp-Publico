"""Cliente HTTP do Kommo.

Le as credenciais de config.json. Funciona de dois jeitos:
- token de longa duracao (gravado pelo token_longo.py): usado ate vencer;
  quando vence, o erro explica como gerar outro;
- OAuth2 (gravado pelo auth.py): o access_token e renovado sozinho com o
  refresh_token quando expira.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx

CONFIG_PATH = Path(__file__).parent / "config.json"


class KommoConfigError(RuntimeError):
    """Erro de configuracao/credenciais ausentes ou invalidas."""


def _load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise KommoConfigError(
            f"Arquivo de configuracao nao encontrado: {CONFIG_PATH}. "
            "Copie config.example.json para config.json e rode 'uv run python auth.py'."
        )
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _save_config(cfg: dict[str, Any]) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def _base_url(cfg: dict[str, Any]) -> str:
    sub = cfg.get("subdomain", "").strip()
    if not sub:
        raise KommoConfigError("Campo 'subdomain' ausente no config.json.")
    return f"https://{sub}.kommo.com"


def _refresh_access_token(cfg: dict[str, Any]) -> dict[str, Any]:
    """Troca o refresh_token por um novo access_token e grava no config."""
    if cfg.get("long_lived"):
        vence = time.strftime("%d/%m/%Y", time.localtime(int(cfg.get("expires_at", 0)) + 120))
        raise KommoConfigError(
            f"O token de longa duracao venceu ou foi revogado (validade: {vence}). "
            "Gere outro na integracao do Kommo (aba 'Chaves e escopos') e rode "
            "'uv run python token_longo.py'."
        )
    if not cfg.get("refresh_token"):
        raise KommoConfigError(
            "Sem refresh_token. Rode 'uv run python auth.py' para autenticar."
        )
    resp = httpx.post(
        f"{_base_url(cfg)}/oauth2/access_token",
        json={
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
            "grant_type": "refresh_token",
            "refresh_token": cfg["refresh_token"],
            "redirect_uri": cfg.get("redirect_uri", "https://localhost"),
        },
        timeout=30,
    )
    if resp.status_code != 200:
        raise KommoConfigError(
            f"Falha ao renovar token ({resp.status_code}): {resp.text}"
        )
    data = resp.json()
    cfg["access_token"] = data["access_token"]
    cfg["refresh_token"] = data["refresh_token"]
    cfg["expires_at"] = int(time.time()) + int(data.get("expires_in", 86400)) - 120
    _save_config(cfg)
    return cfg


def _ensure_token(cfg: dict[str, Any]) -> dict[str, Any]:
    if not cfg.get("access_token"):
        return _refresh_access_token(cfg)
    if int(cfg.get("expires_at", 0)) <= int(time.time()):
        return _refresh_access_token(cfg)
    return cfg


def request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: Any | None = None,
) -> Any:
    """Faz uma requisicao autenticada na API v4 do Kommo.

    `path` pode vir com ou sem o prefixo /api/v4. Renova o token e tenta
    uma vez de novo em caso de 401.
    """
    cfg = _ensure_token(_load_config())

    if not path.startswith("/"):
        path = "/" + path
    if not path.startswith("/api/"):
        path = "/api/v4" + path

    def _do(token: str) -> httpx.Response:
        return httpx.request(
            method.upper(),
            f"{_base_url(cfg)}{path}",
            params=params,
            json=json_body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=60,
        )

    resp = _do(cfg["access_token"])
    if resp.status_code == 401:
        cfg = _refresh_access_token(cfg)
        resp = _do(cfg["access_token"])

    if resp.status_code == 204 or not resp.content:
        return {"status": resp.status_code, "ok": resp.is_success}

    try:
        data = resp.json()
    except Exception:
        return {"status": resp.status_code, "text": resp.text}

    if not resp.is_success:
        raise RuntimeError(f"Kommo API {resp.status_code}: {json.dumps(data, ensure_ascii=False)}")
    return data
