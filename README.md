# AuditIA Backend

Backend independiente para AuditIA, construido con FastAPI, MongoDB y Beanie para reemplazar progresivamente los datos simulados del frontend React/Vite.

## Stack

- Python 3.11+
- FastAPI
- Uvicorn
- MongoDB
- Beanie ODM
- JWT con `python-jose`
- Passlib + Bcrypt
- Pydantic Settings

## Instalacion

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Configura MongoDB en `.env`:

```bash
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=auditoria_siniestros
```

No escribas secretos reales en archivos versionados. Para OpenAI usa `OPENAI_API_KEY` solo en tu `.env` local.

## Ejecucion

```bash
uvicorn app.main:app --reload
```

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
- Healthcheck: `http://localhost:8000/health`

## Integracion con frontend

El frontend debe apuntar a:

```bash
VITE_API_BASE_URL=http://localhost:8000/api
```

El frontend actual aun no envia JWT. Por compatibilidad local, `AUTH_REQUIRED=false` por defecto. En produccion usa:

```bash
AUTH_REQUIRED=true
JWT_SECRET_KEY=un-secreto-largo-y-seguro
```

## Endpoints principales

### Autenticacion

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

### Casos

- `GET /api/cases`
- `POST /api/cases`
- `GET /api/cases/{caseId}`
- `PATCH /api/cases/{caseId}/status`
- `GET /api/cases/{caseId}/documents`
- `POST /api/cases/{caseId}/documents`

### Auditorias

- `POST /api/audit/{caseId}`
- `GET /api/audit/{caseId}/latest`
- `GET /api/audit/{caseId}/history`

### Reglas de negocio

- `GET /api/business-rules`
- `POST /api/business-rules`
- `PUT /api/business-rules/{ruleId}`
- `PATCH /api/business-rules/{ruleId}/toggle`
- `DELETE /api/business-rules/{ruleId}`

### Estadisticas

- `GET /api/statistics/dashboard`
- `GET /api/statistics/denial-reasons`

## Respuestas vacias

Si no hay datos reales, la API devuelve ceros, listas vacias o `null`. No se generan datos falsos.

## Estructura

```text
app/
  main.py
  core/
  database/
  auth/
  users/
  cases/
  audits/
  reports/
  analytics/
  dashboard/
  shared/
```

## Notas de seguridad

- Rota cualquier API key que haya sido expuesta accidentalmente.
- Usa `.env` local para secretos.
- Cambia `JWT_SECRET_KEY` antes de activar `AUTH_REQUIRED=true`.
