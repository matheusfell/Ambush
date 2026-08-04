# AmbushSystem — Fases 1–3

Monitoramento interno de disponibilidade (escritório).

| Fase | Conteúdo |
|---|---|
| 1 | Checagens HTTP, monitores, agendador, logs |
| 2 | Incidentes, SMTP, grupos, anti-flood |
| 3 | **JWT + dashboard React** |

## Subida rápida

### Backend

```powershell
$env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
cd AmbushSystem
Copy-Item .env.example .env   # se ainda não tiver
# preencha ENCRYPTION_KEY e JWT_SECRET

docker compose up -d
cd backend
uv sync --extra dev
uv run alembic upgrade head

# UM único worker
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Admin seed (só na primeira subida, se `users` vazia):

- usuário: `admin` (ou `ADMIN_USERNAME`)
- senha: `admin123` (ou `ADMIN_PASSWORD`) — **troque em produção**

### Frontend

```powershell
cd AmbushSystem\frontend
npm install
npm run dev
```

Abra http://localhost:5173 — o Vite faz proxy de `/api` → `:8000`.

### Frontend acoplado ao backend

Para servir a interface pelo próprio FastAPI em uma única porta:

```powershell
cd AmbushSystem\frontend
npm install
npm run build

cd ..\backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Depois acesse http://localhost:8000. As rotas `/api/*` continuam sendo API, e as
rotas do React, como `/monitors/1`, são entregues pelo fallback do backend.

## Dashboard (Fase 3)

- Contadores: online / degradado / fora / pausado
- Cards por monitor com barra de histórico limitada às últimas 36 checagens
- Agrupamento por tag
- Polling a cada 30s
- Admin: “Checar agora” e pausar/retomar no card
- Viewer: só visualiza

Direção visual: console operacional escuro, IBM Plex Sans/Mono, status com **cor + ícone** (daltonismo).

## Auth

```http
POST /api/auth/login   { "username", "password" } → { access_token }
GET  /api/auth/me      Bearer token
POST /api/auth/users   admin cria usuários (role: admin|viewer)
```

Endpoints de leitura exigem login; mutações exigem `admin`.  
`GET /api/health` permanece aberto.

## E-mail de alerta

Na aba **E-mail**, o admin configura:

- Conexão global de envio:
  - **Microsoft 365 Graph** (recomendado): `Tenant ID`, `Client ID`, `Client Secret` e remetente.
  - **SMTP legado/relay interno**: `host`, porta, usuário, senha e TLS.
- Alerta por monitor: destinatários, assunto/corpo e quantas checagens `DOWN` seguidas são necessárias para enviar.

Por padrão, o alerta só é disparado após **3 checagens `DOWN` consecutivas**. Variáveis aceitas nos templates: `{monitor_name}`, `{url}`, `{error}`, `{status_code}`, `{failure_count}`, `{duration}` e `{dashboard_url}`.

Para O365 Graph, o App Registration precisa da permissão Application `Mail.Send` com consentimento administrativo. Secrets podem ser carregados inicialmente pelo `.env` (`O365_TENANT_ID`, `O365_CLIENT_ID`, `O365_CLIENT_SECRET`, `EMAIL_FROM_ADDR`) e ficam criptografados quando salvos pelo painel.

## Testes backend

```powershell
cd backend
uv run pytest -q
uv run ruff check app tests
uv run mypy app
```

## Próximas fases

- **Fase 4:** detalhe do monitor, gráficos, filtros de log, telas de config
- **Fase 5:** Docker Compose completo, retenção, deploy na VM
