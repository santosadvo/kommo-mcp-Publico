"""Servidor MCP para acesso total ao Kommo CRM.

Expoe ferramentas para leads, contatos, empresas, tarefas, notas, funis,
usuarios e campos personalizados — alem de uma ferramenta generica
(kommo_request) que alcanca qualquer endpoint da API v4.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

import kommo_client as kc

mcp = FastMCP("kommo")


# --------------------------------------------------------------------------
# Generico — acesso total a qualquer endpoint da API v4
# --------------------------------------------------------------------------
@mcp.tool()
def kommo_request(
    method: str,
    path: str,
    params: dict[str, Any] | None = None,
    body: Any | None = None,
) -> Any:
    """Chama qualquer endpoint da API v4 do Kommo (acesso total).

    method: GET, POST, PATCH, DELETE.
    path: caminho do endpoint, ex. "/leads", "/contacts/123", "/account".
          O prefixo /api/v4 e adicionado automaticamente se ausente.
    params: parametros de query (ex. {"query": "Joao", "limit": 50}).
    body: corpo JSON para POST/PATCH (lista ou objeto, conforme a API).
    """
    return kc.request(method, path, params=params, json_body=body)


# --------------------------------------------------------------------------
# Conta / metadados
# --------------------------------------------------------------------------
@mcp.tool()
def kommo_account_info() -> Any:
    """Retorna dados da conta Kommo (nome, subdominio, moeda, etc.)."""
    return kc.request("GET", "/account")


@mcp.tool()
def kommo_list_users() -> Any:
    """Lista os usuarios (operadores) da conta."""
    return kc.request("GET", "/users")


@mcp.tool()
def kommo_list_pipelines() -> Any:
    """Lista os funis (pipelines) e suas etapas/status."""
    return kc.request("GET", "/leads/pipelines")


@mcp.tool()
def kommo_list_custom_fields(entity: str) -> Any:
    """Lista campos personalizados de uma entidade.

    entity: "leads", "contacts", "companies" ou "customers".
    """
    return kc.request("GET", f"/{entity}/custom_fields")


# --------------------------------------------------------------------------
# Leads
# --------------------------------------------------------------------------
@mcp.tool()
def kommo_list_leads(
    query: str | None = None,
    page: int = 1,
    limit: int = 50,
    with_: str | None = "contacts",
) -> Any:
    """Lista/busca leads.

    query: texto de busca (nome, telefone, e-mail, etc.).
    limit: ate 250 por pagina.
    with_: dados extras a incluir, ex. "contacts,companies".
    """
    params: dict[str, Any] = {"page": page, "limit": limit}
    if query:
        params["query"] = query
    if with_:
        params["with"] = with_
    return kc.request("GET", "/leads", params=params)


@mcp.tool()
def kommo_get_lead(lead_id: int, with_: str | None = "contacts,companies") -> Any:
    """Retorna um lead pelo ID, com contatos/empresas vinculados."""
    params = {"with": with_} if with_ else None
    return kc.request("GET", f"/leads/{lead_id}", params=params)


@mcp.tool()
def kommo_create_leads(leads: list[dict[str, Any]]) -> Any:
    """Cria um ou mais leads.

    leads: lista de objetos, ex.
        [{"name": "Novo cliente", "price": 5000, "status_id": 12345}]
    """
    return kc.request("POST", "/leads", json_body=leads)


@mcp.tool()
def kommo_update_lead(lead_id: int, fields: dict[str, Any]) -> Any:
    """Atualiza um lead (mover de etapa, mudar valor, responsavel, etc.).

    fields: campos a alterar, ex. {"status_id": 9999, "price": 8000}.
    """
    return kc.request("PATCH", f"/leads/{lead_id}", json_body=fields)


# --------------------------------------------------------------------------
# Contatos
# --------------------------------------------------------------------------
@mcp.tool()
def kommo_list_contacts(
    query: str | None = None,
    page: int = 1,
    limit: int = 50,
) -> Any:
    """Lista/busca contatos."""
    params: dict[str, Any] = {"page": page, "limit": limit}
    if query:
        params["query"] = query
    return kc.request("GET", "/contacts", params=params)


@mcp.tool()
def kommo_get_contact(contact_id: int, with_: str | None = "leads") -> Any:
    """Retorna um contato pelo ID."""
    params = {"with": with_} if with_ else None
    return kc.request("GET", f"/contacts/{contact_id}", params=params)


@mcp.tool()
def kommo_create_contacts(contacts: list[dict[str, Any]]) -> Any:
    """Cria um ou mais contatos.

    contacts: lista de objetos, ex.
        [{"name": "Maria", "custom_fields_values": [...]}]
    """
    return kc.request("POST", "/contacts", json_body=contacts)


@mcp.tool()
def kommo_update_contact(contact_id: int, fields: dict[str, Any]) -> Any:
    """Atualiza um contato pelo ID."""
    return kc.request("PATCH", f"/contacts/{contact_id}", json_body=fields)


# --------------------------------------------------------------------------
# Empresas
# --------------------------------------------------------------------------
@mcp.tool()
def kommo_list_companies(
    query: str | None = None,
    page: int = 1,
    limit: int = 50,
) -> Any:
    """Lista/busca empresas."""
    params: dict[str, Any] = {"page": page, "limit": limit}
    if query:
        params["query"] = query
    return kc.request("GET", "/companies", params=params)


@mcp.tool()
def kommo_create_companies(companies: list[dict[str, Any]]) -> Any:
    """Cria uma ou mais empresas."""
    return kc.request("POST", "/companies", json_body=companies)


# --------------------------------------------------------------------------
# Tarefas
# --------------------------------------------------------------------------
@mcp.tool()
def kommo_list_tasks(page: int = 1, limit: int = 50) -> Any:
    """Lista tarefas."""
    return kc.request("GET", "/tasks", params={"page": page, "limit": limit})


@mcp.tool()
def kommo_create_tasks(tasks: list[dict[str, Any]]) -> Any:
    """Cria uma ou mais tarefas.

    tasks: lista de objetos, ex.
        [{"text": "Ligar para o cliente", "complete_till": 1718500000,
          "entity_id": 12345, "entity_type": "leads"}]
    complete_till e um timestamp Unix (segundos).
    """
    return kc.request("POST", "/tasks", json_body=tasks)


@mcp.tool()
def kommo_complete_task(task_id: int, result_text: str = "Concluida") -> Any:
    """Marca uma tarefa como concluida com um texto de resultado."""
    return kc.request(
        "PATCH",
        f"/tasks/{task_id}",
        json_body={"is_completed": True, "result": {"text": result_text}},
    )


# --------------------------------------------------------------------------
# Notas
# --------------------------------------------------------------------------
@mcp.tool()
def kommo_list_notes(entity_type: str, entity_id: int) -> Any:
    """Lista notas de uma entidade.

    entity_type: "leads", "contacts" ou "companies".
    """
    return kc.request("GET", f"/{entity_type}/{entity_id}/notes")


@mcp.tool()
def kommo_add_note(entity_type: str, entity_id: int, text: str) -> Any:
    """Adiciona uma nota de texto comum a uma entidade.

    entity_type: "leads", "contacts" ou "companies".
    """
    body = [{"note_type": "common", "params": {"text": text}}]
    return kc.request("POST", f"/{entity_type}/{entity_id}/notes", json_body=body)


if __name__ == "__main__":
    mcp.run()
