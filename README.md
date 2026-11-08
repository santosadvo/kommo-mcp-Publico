# kommo-mcp

**Tutorial: como dar ao Claude Code acesso de leitura e escrita ao seu Kommo CRM** (leads, contatos, empresas, tarefas, notas, funis e campos personalizados), usando a API v4 oficial.

Serve para quem usa o Kommo no dia a dia e quer pedir ao Claude coisas como "liste os leads parados há mais de 7 dias", "crie uma tarefa de retorno para este contato" ou "registre uma nota neste lead". Não precisa saber programar.

Além das ferramentas prontas, existe a `kommo_request`, que chama qualquer endpoint da API v4.

## O que você precisa

- [uv](https://docs.astral.sh/uv/) instalado (ele baixa o Python e as dependências sozinho). No Mac: `brew install uv`.
- [Claude Code](https://claude.com/claude-code) instalado.
- Uma conta Kommo com permissão de administrador (para criar a integração).

## Passo a passo (uma vez só)

### 1. Descobrir o subdomínio da sua conta

É a primeira parte do endereço que você usa para entrar no Kommo. Se você acessa `https://suaempresa.kommo.com`, o subdomínio é `suaempresa`. Anote, vai no `config.json`.

### 2. Criar a integração no Kommo

Em **Configurações → Central de integrações → Criar integração**:

- **URL de redirecionamento:** `https://localhost`
- Marque **Permitir acesso: Todas**
- Dê um **Nome** (por exemplo, "Claude MCP") e salve.

Depois de salvar, abra a integração e vá na aba **Chaves e escopos**. Copie:

- **ID da integração** → `client_id`
- **Chave secreta** → `client_secret`
- Clique no botão para gerar e copiar o **código de autorização** (vale por cerca de 20 minutos).

### 3. Instalar e preencher as credenciais

```bash
git clone https://github.com/santosadvo/kommo-mcp-Publico.git
cd kommo-mcp-Publico
cp config.example.json config.json
```

Abra o `config.json` e preencha `subdomain`, `client_id` e `client_secret`. Salve.

### 4. Autenticar

Com o código de autorização copiado (rode logo, ele expira em 20 minutos):

```bash
uv run python auth.py "COLE_O_CODIGO_AQUI"
```

Isso grava `access_token` e `refresh_token` no `config.json`. Dali em diante o servidor renova o token sozinho (o refresh dura cerca de 3 meses).

### 5. Registrar no Claude Code

Pelo terminal (troque o caminho pelo da pasta onde você clonou):

```bash
claude mcp add kommo -- uv run --directory /caminho/para/kommo-mcp-Publico python server.py
```

Ou, editando o `~/.claude.json`, dentro de `mcpServers`:

```json
"kommo": {
  "command": "uv",
  "args": ["run", "--directory", "/caminho/para/kommo-mcp-Publico", "python", "server.py"]
}
```

Reinicie o Claude Code e as ferramentas `kommo_*` aparecem.

## Teste rápido (sem o Claude)

```bash
uv run python -c "import kommo_client as k; print(k.request('GET','/account')['name'])"
```

Deve imprimir o nome da sua conta Kommo.

## Ferramentas

- **Conta:** `kommo_account_info`, `kommo_list_users`, `kommo_list_pipelines`, `kommo_list_custom_fields`
- **Leads:** `kommo_list_leads`, `kommo_get_lead`, `kommo_create_leads`, `kommo_update_lead`
- **Contatos e empresas:** `kommo_list_contacts`, `kommo_get_contact`, `kommo_create_contacts`, `kommo_update_contact`, `kommo_list_companies`, `kommo_create_companies`
- **Tarefas e notas:** `kommo_list_tasks`, `kommo_create_tasks`, `kommo_complete_task`, `kommo_list_notes`, `kommo_add_note`
- **Acesso total:** `kommo_request` (qualquer endpoint da API v4)

## Segurança

- O `config.json` guarda suas credenciais e tokens e está no `.gitignore`. Nunca o envie para o git, nem cole o conteúdo em conversas ou prints.
- O acesso configurado é total (leitura e escrita). Deixe o Claude Code pedir confirmação antes de cada ação de escrita, conforme o modo de permissão que você escolher.
- Se suspeitar de vazamento, apague a integração no Kommo e crie outra.

## Limites

- O código de autorização vale cerca de 20 minutos; se expirar, gere outro.
- Se ficar mais de 3 meses sem usar, o refresh token expira e é preciso rodar o `auth.py` de novo com um código novo.
- A API do Kommo limita o número de requisições por segundo; em listas grandes, peça por partes.
