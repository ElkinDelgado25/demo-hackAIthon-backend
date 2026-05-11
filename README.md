# AuditIA Backend

Backend independiente para AuditIA. Expone una API REST con FastAPI para conectar el frontend React/Vite con datos reales en MongoDB, reemplazando progresivamente mocks y datos hardcodeados.

## Estado Actual Del Proyecto

El backend contiene:

- API FastAPI bajo el prefijo `/api`.
- MongoDB con Beanie ODM.
- Autenticacion JWT con `python-jose`.
- Hash de passwords con Passlib/Bcrypt.
- Configuracion centralizada con Pydantic Settings.
- CORS para el frontend Vite.
- Manejo global de errores.
- Modulos separados por dominio: auth, users, cases, audits, business rules, dashboard, database y shared.
- Servicio IA en `app/shared/ai_service.py` usando LangChain/OpenAI.
- Parser de archivos en `app/shared/file_parser.py` para PDF, JSON, CSV y texto plano.
- Script auxiliar `test_openai.py` para verificar configuracion de OpenAI.

## Requisito Importante De Python

Este proyecto usa `StrEnum` en `app/shared/enums.py`, por lo tanto requiere:

```bash
Python 3.11+
```

Si ejecutas el backend con Python 3.10, varios imports fallaran con:

```text
ImportError: cannot import name 'StrEnum' from 'enum'
```

Soluciones:

- Recomendada: instalar y usar Python 3.11 o superior.
- Alternativa: cambiar `StrEnum` por `str, Enum` en `app/shared/enums.py` si quieres soportar Python 3.10.

## Stack

- Python 3.11+
- FastAPI
- Uvicorn
- MongoDB
- Motor
- Beanie ODM
- Pydantic v2
- Pydantic Settings
- JWT con `python-jose`
- Passlib + Bcrypt
- LangChain
- LangChain OpenAI
- OpenAI SDK
- PyPDF2

## Instalacion

Desde la carpeta del backend:

```bash
py -3.13 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
```

Si cambiaste `requirements.txt`, vuelve a ejecutar:

```bash
python -m pip install -r requirements.txt
```

## Variables De Entorno

Configura `.env` tomando como base `.env.example`.

```bash
APP_NAME=AuditIA API
ENVIRONMENT=development
API_PREFIX=/api
BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=auditoria_siniestros

AUTH_REQUIRED=false
JWT_SECRET_KEY=change-me-use-a-long-random-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

UPLOAD_MAX_TOTAL_BYTES=20971520
UPLOAD_ALLOWED_EXTENSIONS=pdf,csv,xlsx,json,png,jpg,jpeg
UPLOAD_LOCAL_DIR=storage/uploads

DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=change-me
DEFAULT_ADMIN_FULL_NAME=AuditIA Admin

OPENAI_API_KEY=
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.1
CHROMA_COLLECTION=auditia_documents
```

No guardes claves reales en Git. Si una API key fue expuesta, rotala desde el proveedor y usa la nueva solo en `.env`.

## Ejecucion Local

Primero levanta MongoDB. Luego:

```bash
.venv\Scripts\activate
python --version
uvicorn app.main:app --reload
```

El comando `python --version` debe mostrar Python 3.13.x.

URLs:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/api/openapi.json`
- Healthcheck: `http://localhost:8000/health`

## Deploy En Render

Este repo incluye `.python-version` con:

```text
3.13.4
```

Tambien incluye `runtime.txt` con:

```text
python-3.13.4
```

Render debe usar Python 3.13.4. No uses Python 3.14 para este proyecto por ahora, porque `pydantic-core==2.27.2` puede intentar compilarse con Rust durante el build y fallar en Render.

En Render configura:

```bash
Build Command: pip install -r requirements.txt
Start Command: python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Variables necesarias en Render:

```bash
MONGODB_URI=mongodb+srv://...
MONGODB_DB=auditoria_siniestros
JWT_SECRET_KEY=un-secreto-largo-y-seguro
AUTH_REQUIRED=false
BACKEND_CORS_ORIGINS=https://tu-frontend.onrender.com,http://localhost:5173
OPENAI_API_KEY=...
```

Si Render sigue usando Python 3.14, agrega tambien una variable de entorno:

```bash
PYTHON_VERSION=3.13.4
```

Luego ejecuta un nuevo deploy con cache limpia.

## Integracion Con Frontend

El frontend debe apuntar a:

```bash
VITE_API_BASE_URL=http://localhost:8000/api
```

El frontend actual puede operar en desarrollo sin token porque:

```bash
AUTH_REQUIRED=false
```

Para produccion:

```bash
AUTH_REQUIRED=true
JWT_SECRET_KEY=un-secreto-largo-y-seguro
```

Cuando `AUTH_REQUIRED=true`, los endpoints protegidos esperan:

```http
Authorization: Bearer <access_token>
```

## Arquitectura

```text
app/
  main.py
  core/
    config.py
    dependencies.py
    exceptions.py
    security.py
  database/
    mongo.py
    init_db.py
  auth/
    routes.py
    schemas.py
    service.py
  users/
    models.py
    schemas.py
    service.py
  cases/
    models.py
    routes.py
    schemas.py
    service.py
  audits/
    models.py
    routes.py
    schemas.py
    service.py
  business_rules/
    models.py
    routes.py
    schemas.py
    service.py
  dashboard/
    routes.py
    schemas.py
    service.py
  shared/
    ai_service.py
    enums.py
    file_parser.py
    schemas.py
  analytics/
  reports/
```

## Modulos Principales

### Auth

Gestiona registro, login, token JWT y usuario actual.

### Users

Modelo de usuario, roles basicos y usuario administrador inicial.

### Cases

Gestion de casos/siniestros, consulta por `_id` o `claimNumber`, estados y documentos asociados.

### Audits

Ejecucion de auditorias, validacion de documentos obligatorios, historial y ultimo resultado.

### Business Rules

CRUD de reglas de negocio, toggle `ACTIVA`/`INACTIVA` y reglas usadas por el motor de auditoria.

### Dashboard

Metricas agregadas, ultimas auditorias y razones de denegacion.

### Shared AI

`AIService` usa LangChain/OpenAI para:

- Extraer items desde texto de facturas.
- Detectar anomalias.
- Devolver JSON estructurado para auditoria.

### File Parser

`FileParser` extrae texto desde:

- PDF
- JSON
- CSV
- Texto plano como fallback

## Endpoints

### Health

- `GET /health`

### Autenticacion

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

### Casos

- `GET /api/cases`
- `POST /api/cases`
- `GET /api/cases/{case_id}`
- `PATCH /api/cases/{case_id}/status`
- `GET /api/cases/{case_id}/documents`
- `POST /api/cases/{case_id}/documents`

### Auditorias

- `POST /api/audit/{case_id}`
- `GET /api/audit/{case_id}/latest`
- `GET /api/audit/{case_id}/history`

### Reglas De Negocio

- `GET /api/business-rules`
- `POST /api/business-rules`
- `PUT /api/business-rules/{rule_id}`
- `PATCH /api/business-rules/{rule_id}/toggle`
- `DELETE /api/business-rules/{rule_id}`

### Estadisticas

- `GET /api/statistics/dashboard`
- `GET /api/statistics/denial-reasons`

## Contratos Esperados Por El Frontend

Las respuestas usan aliases `camelCase` para coincidir con React:

- `claimNumber`
- `reportedDamages`
- `invoiceTotal`
- `tariffTotal`
- `receivedAt`
- `createdAt`
- `documentType`
- `mimeType`
- `auditId`
- `caseId`
- `latestAudits`
- `approvalRate`
- `targetField`
- `referenceValue`
- `alertMessage`

## Estados Y Enums

Estados de caso:

- `NUEVO`
- `PENDIENTE_DOCUMENTOS`
- `LISTO_PARA_AUDITORIA`
- `EN_AUDITORIA`
- `OBSERVADO`
- `APROBADO`
- `DENEGADO`
- `REVISION_HUMANA`

Tipos de documento:

- `FACTURA`
- `ORDEN_REPARACION`
- `DETALLE_MANO_OBRA`
- `FOTOS_DANIO`

Tipos de regla:

- `PRECIO_MAXIMO`
- `ITEM_DUPLICADO`
- `ITEM_NO_RELACIONADO`
- `CANTIDAD_MAXIMA`
- `DOCUMENTO_OBLIGATORIO`
- `PORCENTAJE_VARIACION`

## Carga De Documentos

Endpoint:

```http
POST /api/cases/{case_id}/documents
```

Tipo:

```text
multipart/form-data
```

Campos:

- `files`: uno o varios archivos.
- `documents`: JSON serializado con metadata.

Ejemplo de `documents`:

```json
[
  {
    "name": "factura.pdf",
    "type": "FACTURA",
    "size": 123456,
    "mimeType": "application/pdf"
  }
]
```

Formatos permitidos:

- PDF
- CSV
- XLSX
- JSON
- PNG
- JPG
- JPEG

Tamano maximo total por caso/auditoria:

```bash
UPLOAD_MAX_TOTAL_BYTES=20971520
```

## Reglas De Auditoria Implementadas

La primera version del motor:

- Exige documentos obligatorios antes de auditar.
- Carga reglas `ACTIVA`.
- Evalua reglas de tipo `DOCUMENTO_OBLIGATORIO`.
- Genera discrepancias.
- Actualiza estado del caso.
- Guarda historial de auditoria.
- Calcula confianza basica.

Si no existen datos, la API devuelve ceros, listas vacias o `null`. No se generan datos falsos.

## Verificacion De Importaciones

Para revisar importaciones de todos los archivos:

```bash
.venv\Scripts\activate
python -m compileall app test_openai.py
```

Para importar modulo por modulo:

```powershell
@'
import importlib
from pathlib import Path

failures = []
for path in sorted(Path(".").rglob("*.py")):
    if any(part in {".venv", "__pycache__"} for part in path.parts):
        continue
    module = ".".join(path.with_suffix("").parts)
    try:
        importlib.import_module(module)
        print(f"OK {module}")
    except Exception as exc:
        failures.append((module, type(exc).__name__, str(exc)))
        print(f"FAIL {module}: {type(exc).__name__}: {exc}")

print("failures=", len(failures))
for failure in failures:
    print(failure)
'@ | .venv\Scripts\python -
```

Si aparece `StrEnum`, revisa que estes usando Python 3.11+.

## Verificacion De OpenAI

El archivo `test_openai.py` verifica que la configuracion exista:

```bash
.venv\Scripts\python test_openai.py
```

Este script no debe imprimir la API key completa. Solo confirma si existe, el modelo y la temperatura.

## Verificacion De Dependencias

```bash
.venv\Scripts\python -m pip check
```

Si `app/shared/ai_service.py` falla al importar, confirma que esten instaladas:

```bash
langchain
langchain-community
langchain-openai
openai
```

Todas estan declaradas en `requirements.txt`.

## MongoDB

La conexion se inicializa en startup mediante:

```text
app/database/mongo.py
```

Modelos registrados en Beanie:

- `User`
- `Case`
- `CaseDocument`
- `Audit`
- `BusinessRule`

Tambien se crea un admin por defecto si no existe, usando:

```bash
DEFAULT_ADMIN_EMAIL
DEFAULT_ADMIN_PASSWORD
DEFAULT_ADMIN_FULL_NAME
```

## Seguridad

- No versionar `.env`.
- Rotar claves expuestas.
- Cambiar `JWT_SECRET_KEY` en produccion.
- Activar `AUTH_REQUIRED=true` en produccion.
- Mantener `OPENAI_API_KEY` solo en entorno local o gestor de secretos.

## Problemas Comunes

### `ImportError: cannot import name 'StrEnum'`

Estas usando Python 3.10 o menor. Usa Python 3.11+ o adapta enums a `str, Enum`.

### `ModuleNotFoundError: langchain_openai`

Ejecuta:

```bash
python -m pip install -r requirements.txt
```

### Error de Passlib con bcrypt 5

Si aparece:

```text
error reading bcrypt version
ValueError: password cannot be longer than 72 bytes
```

Instala la version compatible:

```bash
python -m pip install bcrypt==4.0.1
```

`passlib==1.7.4` no es compatible con `bcrypt==5.0.0`. Por eso `requirements.txt` fija `bcrypt==4.0.1`.

### MongoDB no conecta

Verifica:

- MongoDB esta levantado.
- `MONGODB_URI` es correcto.
- `MONGODB_DB` existe o puede crearse.

### El frontend no conecta

Verifica:

- Backend en `http://localhost:8000`.
- Frontend con `VITE_API_BASE_URL=http://localhost:8000/api`.
- CORS incluye `http://localhost:5173`.
