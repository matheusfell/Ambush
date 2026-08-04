# AmbushSystem — Fases 1 e 2

Monitoramento interno de disponibilidade de sistemas (escritório).

- **Fase 1:** checagens HTTP, CRUD de monitores, agendador, logs  
- **Fase 2:** incidentes, SMTP, grupos de destinatários, anti-flood / quiet hours  

Sem UI ainda (React = Fase 3). Validação via API / PowerShell / `/docs`.

## Pré-requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — se o terminal não achar: `$env:Path = "$env:USERPROFILE\.local\bin;$env:Path"`
- Docker Desktop (Postgres)

## Subida rápida

```powershell
cd AmbushSystem
Copy-Item .env.example .env
# Gere ENCRYPTION_KEY e cole no .env:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

docker compose up -d
cd backend
uv sync --extra dev
uv run alembic upgrade head

# UM único worker — o agendador vive neste processo
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- Health: http://localhost:8000/api/health  
- Docs: http://localhost:8000/docs  

## Fase 2 — configurar alertas

### 1. Grupo de destinatários

```powershell
$body = @{
  name = "TI"
  emails = @("seu.email@reis.adv.br")
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/notification-groups `
  -ContentType "application/json" -Body $body
```

### 2. SMTP (Microsoft 365 ou relay interno)

```powershell
$smtp = @{
  host = "smtp.office365.com"
  port = 587
  username = "noreply@reis.adv.br"
  password = "SUA_SENHA"
  from_email = "noreply@reis.adv.br"
  from_name = "AmbushSystem"
  use_tls = $true
} | ConvertTo-Json

Invoke-RestMethod -Method Put -Uri http://localhost:8000/api/settings/smtp `
  -ContentType "application/json" -Body $smtp

# Teste (mostra o erro real do SMTP se falhar)
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/settings/smtp/test `
  -ContentType "application/json" `
  -Body (@{ to_email = "seu.email@reis.adv.br" } | ConvertTo-Json)
```

> Porta **587** + `use_tls=true` → STARTTLS. Porta **465** → TLS implícito automático.

### 3. Vincular grupo ao monitor

```powershell
Invoke-RestMethod -Method Put -Uri http://localhost:8000/api/monitors/1 `
  -ContentType "application/json" `
  -Body (@{ notification_group_id = 1 } | ConvertTo-Json)
```

### 4. Regras globais (anti-flood / quiet hours)

```powershell
Invoke-RestMethod http://localhost:8000/api/settings/notification-rules

$rules = @{
  on_down = $true
  on_recovery = $true
  on_degraded = $false
  min_interval_minutes = 30
  reminder_minutes = 60
  quiet_hours_start = "22:00:00"
  quiet_hours_end = "06:00:00"
} | ConvertTo-Json

Invoke-RestMethod -Method Put -Uri http://localhost:8000/api/settings/notification-rules `
  -ContentType "application/json" -Body $rules
```

### 5. Incidentes

```powershell
Invoke-RestMethod "http://localhost:8000/api/incidents?status=open"
Invoke-RestMethod http://localhost:8000/api/incidents/1
```

Para forçar um incidente em teste: aponte um monitor para uma URL inválida, rode `POST /api/monitors/{id}/check`, depois corrija e cheque de novo para ver o `[RESTABELECIDO]`.

## Validação Fase 1 (monitores)

```powershell
Invoke-RestMethod http://localhost:8000/api/health
Invoke-RestMethod http://localhost:8000/api/monitors
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/monitors/1/check
Invoke-RestMethod "http://localhost:8000/api/monitors/1/checks?page=1"
```

> Certificados: o checker usa o trust store do sistema. Autoassinado sem CA → `skip_tls_verify: true`.

## Testes

```powershell
cd backend
uv run pytest -q
uv run ruff check app tests
uv run mypy app
```

## Arquitetura

| Decisão | Escolha |
|---|---|
| Processo do agendador | 1 worker Uvicorn |
| Scheduler | 1 `asyncio.Task` por monitor + Semaphore |
| HTTP | `httpx.AsyncClient` |
| E-mail | `aiosmtplib` (STARTTLS / SSL 465) |
| Senhas no banco | Fernet (`ENCRYPTION_KEY`) |
| Incidentes | Abre em DOWN, fecha no primeiro UP; anti-flood via `last_notified_at` |

## Próximas fases

- **Fase 3:** React + JWT + dashboard  
- **Fase 4:** detalhe do monitor, gráficos, settings UI  
- **Fase 5:** Docker Compose completo, retenção, deploy na VM
