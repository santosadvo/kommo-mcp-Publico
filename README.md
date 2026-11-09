# Kommo + Claude Code: o seu CRM dentro do Claude

Tutorial passo a passo para dar ao Claude Code **acesso de leitura e escrita ao seu Kommo CRM**: leads, contatos, empresas, tarefas, notas, funis e campos personalizados, pela API v4 oficial.

É exatamente o jeito que usamos no dia a dia. A integração é privada e usa um **token de longa duração**: sem login que expira a cada poucos meses e sem servidor de terceiros no meio. Não precisa saber programar. Leva uns 10 minutos.

## O que você vai conseguir pedir

- "Quantos leads entraram esta semana em cada funil?"
- "Liste os leads parados há mais de 7 dias na etapa Proposta enviada."
- "Crie uma tarefa de retorno para amanhã às 10h neste lead."
- "Registre uma nota neste contato com o resumo da ligação."
- "Mova o lead 12345 para a etapa Contrato assinado."

## Como funciona

```
Você ──► Claude Code ──► servidor MCP (esta pasta, no seu computador) ──► API v4 do Kommo
```

O servidor roda no seu próprio computador e fala direto com o Kommo. O token fica num arquivo local (`config.json`) que nunca vai para o git.

## O que você precisa

- [Claude Code](https://claude.com/claude-code) instalado.
- [uv](https://docs.astral.sh/uv/), que baixa o Python e as dependências sozinho. No Mac: `brew install uv`. No Windows: `winget install astral-sh.uv`.
- Uma conta Kommo com **permissão de administrador**, necessária para criar a integração.

## Passo a passo

### 1. Baixe este repositório

```bash
git clone https://github.com/santosadvo/kommo-mcp-Publico.git kommo-mcp
cd kommo-mcp
```

### 2. Crie a integração privada no Kommo

1. Entre no Kommo e vá em **Configurações → Integrações**.
2. Clique em **Criar integração** (canto superior direito).
3. Preencha:
   - **URL de redirecionamento:** `https://localhost`. Esse caminho não usa a URL, mas o Kommo exige o campo.
   - **Permitir acesso:** marque **Todas**.
   - **Nome:** algo como "Claude".
4. Salve.

### 3. Gere o token de longa duração

1. Abra a integração que você acabou de criar e vá na aba **Chaves e escopos**.
2. Clique para gerar um **token de longa duração** e escolha a validade. Nós escolhemos cerca de dois anos e meio.
3. Copie o token. Guarde-o como uma senha: quem tem o token acessa toda a conta.

### 4. Grave o token

Dentro da pasta `kommo-mcp`:

```bash
uv run python token_longo.py
```

O script faz três coisas:

1. Pede o **subdomínio**: se você entra no Kommo por `https://suaempresa.kommo.com`, o subdomínio é `suaempresa`.
2. Pede o **token**, que não aparece na tela enquanto você cola.
3. Grava os dois no `config.json`, mostra até quando o token vale e testa a conexão.

No fim tem que aparecer `Conexão OK: conta "..."` com o nome da sua conta.

### 5. Registre no Claude Code

Ainda dentro da pasta `kommo-mcp`:

```bash
claude mcp add --scope user kommo -- uv run --directory "$(pwd)" python server.py
```

O `--scope user` deixa o Kommo disponível em qualquer pasta em que você abrir o Claude Code. No Windows (PowerShell), troque `"$(pwd)"` pelo caminho completo da pasta.

### 6. Teste

Feche e abra o Claude Code. Digite `/mcp` e veja se o `kommo` aparece como conectado. Depois pergunte:

> Qual é o nome da minha conta no Kommo e quais são os meus funis?

## Ferramentas disponíveis

- **Conta:** `kommo_account_info`, `kommo_list_users`, `kommo_list_pipelines`, `kommo_list_custom_fields`
- **Leads:** `kommo_list_leads`, `kommo_get_lead`, `kommo_create_leads`, `kommo_update_lead`
- **Contatos e empresas:** `kommo_list_contacts`, `kommo_get_contact`, `kommo_create_contacts`, `kommo_update_contact`, `kommo_list_companies`, `kommo_create_companies`
- **Tarefas e notas:** `kommo_list_tasks`, `kommo_create_tasks`, `kommo_complete_task`, `kommo_list_notes`, `kommo_add_note`
- **Acesso total:** `kommo_request`, que chama qualquer endpoint da [API v4 do Kommo](https://developers.kommo.com/)

## Quando o token vencer

O Claude vai avisar com uma mensagem clara. Gere outro token na mesma aba **Chaves e escopos**, rode `uv run python token_longo.py` de novo e reinicie o Claude Code.

Para ver até quando o token atual vale:

```bash
python3 -c "import json,datetime;c=json.load(open('config.json'));print(f\"{datetime.datetime.fromtimestamp(c['expires_at']):%d/%m/%Y}\")"
```

## Alternativa: login OAuth (`auth.py`)

Serve para quem prefere tokens curtos renovados automaticamente em vez do token de longa duração:

1. Na aba **Chaves e escopos**, copie o **ID da integração** e a **chave secreta**.
2. Gere o **código de autorização**, que vale cerca de 20 minutos.
3. Copie o modelo do arquivo de configuração:

   ```bash
   cp config.example.json config.json
   ```

4. No `config.json`, preencha `subdomain`, `client_id` e `client_secret`.
5. Rode o login com o código:

   ```bash
   uv run python auth.py "COLE_O_CODIGO_AQUI"
   ```

Daí em diante o servidor renova o acesso sozinho. Se ficar uns 3 meses sem usar, o refresh vence e é preciso repetir o processo com um código novo.

## Arquivos

| Arquivo | Para que serve |
|---|---|
| `server.py` | As ferramentas que o Claude enxerga |
| `kommo_client.py` | Faz as chamadas à API, lê o token e trata o vencimento |
| `token_longo.py` | Grava o token de longa duração e testa a conexão |
| `auth.py` | Alternativa: login OAuth |
| `config.example.json` | Modelo do arquivo de configuração |
| `config.json` | Criado por você, com o token. **Nunca vai para o git.** |

## Segurança

- O `config.json` guarda o token e está no `.gitignore`. Nunca o envie para o git e não cole o conteúdo em conversas, prints ou planilhas. O `token_longo.py` deixa o arquivo legível só pelo seu usuário.
- O acesso é total (leitura e escrita). Deixe o Claude Code pedir confirmação antes de cada escrita, conforme o modo de permissão que você escolher.
- Se suspeitar de vazamento, revogue o token ou apague a integração no Kommo e gere outro.

## Limites

- A API do Kommo limita quantas requisições cabem por segundo. Em listas grandes, peça por partes ("os próximos 50").
- Este servidor não apaga leads nem contatos por conta própria. Para outras operações da API, existe a `kommo_request`.

## Licença

MIT. Use, adapte e compartilhe à vontade.
