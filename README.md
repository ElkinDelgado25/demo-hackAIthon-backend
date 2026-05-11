# AuditIA Backend

Backend independiente para AuditIA construido con FastAPI, MongoDB y Beanie. Expone una API REST para conectar el frontend React/Vite con datos reales, reemplazando progresivamente mocks, hardcodes y simulaciones.

## Incluye

- FastAPI con Swagger/OpenAPI automatico.
- MongoDB Atlas o local mediante Motor + Beanie.
- Autenticacion JWT con `python-jose`.
- Hash de contrasenas con Passlib + Bcrypt.
- Configuracion con Pydantic Settings.
- CORS configurable para Vite, Vercel o dominios propios.
- Manejo global de errores.
- Validaciones con Pydantic v2.
- Modulos separados por dominio.
- Preparacion para IA con LangChain/OpenAI.
- Parser basico de archivos para PDF, JSON, CSV y texto plano.

## Stack

- Python 3.13.4
- FastAPI
- Uvicorn
- MongoDB
- Motor
- Beanie
- Pydantic v2
- Pydantic Settings
- python-jose
- Passlib + Bcrypt
- LangChain
- OpenAI SDK
- PyPDF2

## Estructura

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
```

## Instalacion Local

Desde la carpeta del backend:

```bash
py -3.13 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
```

Ejecutar:

```bash
python -m uvicorn app.main:app --reload
```

URLs locales:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/api/openapi.json`
- Healthcheck: `http://localhost:8000/health`

## Variables De Entorno

Configura `.env` desde `.env.example`.

```env
APP_NAME=AuditIA API
ENVIRONMENT=development
API_PREFIX=/api
BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

MONGODB_URI=mongodb+srv://usuario:password@cluster.mongodb.net
MONGODB_DB=auditoria_siniestros

AUTH_REQUIRED=false
JWT_SECRET_KEY=change-me-use-a-long-random-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

UPLOAD_MAX_TOTAL_BYTES=20971520
UPLOAD_ALLOWED_EXTENSIONS=pdf,csv,xlsx,json,png,jpg,jpeg,txt
UPLOAD_LOCAL_DIR=storage/uploads

DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=change-me
DEFAULT_ADMIN_FULL_NAME=AuditIA Admin

OPENAI_API_KEY=
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.1
CHROMA_COLLECTION=auditia_documents
```

No guardes claves reales en Git. Si una API key fue expuesta, rotala desde el proveedor y usa la nueva solo como variable de entorno.

## Deploy En Render

El proyecto fija Python 3.13.4 con:

```text
.python-version
runtime.txt
```

Render debe usar Python 3.13.4. No uses Python 3.14 por ahora, porque `pydantic-core==2.27.2` puede intentar compilarse desde Rust durante el build.

Configuracion recomendada en Render:

```bash
Build Command: pip install -r requirements.txt
Start Command: python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Si Render insiste en Python 3.14, agrega:

```env
PYTHON_VERSION=3.13.4
```

Backend desplegado:

```text
https://demo-hackaithon-backend.onrender.com
```

## Integracion Con Frontend

El frontend React/Vite debe usar:

```env
VITE_API_BASE_URL=https://demo-hackaithon-backend.onrender.com/api
```

Para desarrollo local:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

La URL base debe incluir `/api`. El healthcheck no lleva `/api`:

```text
GET /health
```

El frontend no debe guardar credenciales de MongoDB, OpenAI ni secretos JWT. Todo secreto vive en el backend.

## CORS

En Render, `BACKEND_CORS_ORIGINS` debe incluir el dominio real del frontend:

```env
BACKEND_CORS_ORIGINS=https://demo-hack-a-ithon-frontend.vercel.app,http://localhost:5173
```

Si el dominio de Vercel cambia, tambien debe actualizarse esta variable.

## Autenticacion

Endpoints:

```text
POST /api/auth/register
POST /api/auth/login
GET /api/auth/me
```

Login:

```json
{
  "email": "admin@example.com",
  "password": "password"
}
```

Respuesta:

```json
{
  "accessToken": "...",
  "tokenType": "bearer",
  "user": {
    "id": "...",
    "email": "admin@example.com",
    "fullName": "AuditIA Admin",
    "role": "ADMIN",
    "isActive": true
  }
}
```

Cuando `AUTH_REQUIRED=true`, el frontend debe enviar:

```http
Authorization: Bearer <accessToken>
```

En modo demo o desarrollo puede usarse:

```env
AUTH_REQUIRED=false
```

## Endpoints

Health:

```text
GET /health
```

Casos:

```text
GET /api/cases
POST /api/cases
GET /api/cases/{caseId}
PATCH /api/cases/{caseId}/status
GET /api/cases/{caseId}/documents
POST /api/cases/{caseId}/documents
```

Auditorias:

```text
POST /api/audit/batch
POST /api/audit/{caseId}
POST /api/audit/{caseId}/final-verdict
GET /api/audit/{caseId}/latest
GET /api/audit/{caseId}/history
```

Reglas de negocio:

```text
GET /api/business-rules
POST /api/business-rules
PUT /api/business-rules/{ruleId}
PATCH /api/business-rules/{ruleId}/toggle
DELETE /api/business-rules/{ruleId}
```

Estadisticas:

```text
GET /api/statistics/dashboard
GET /api/statistics/denial-reasons
```

## Contrato Para Frontend

La API responde en `camelCase`, aunque internamente Python use `snake_case`.

Ejemplo para crear caso:

```json
{
  "claimNumber": "SIN-2026-001",
  "workshop": "Taller Central",
  "vehicle": {
    "brand": "Toyota",
    "model": "Corolla",
    "year": 2020
  },
  "plate": "ABC-1234",
  "reportedDamages": ["parachoques", "guardafango"],
  "invoiceTotal": 1200,
  "tariffTotal": 1100,
  "status": "NUEVO"
}
```

Respuesta de listado:

```json
{
  "cases": []
}
```

Respuesta de dashboard sin datos:

```json
{
  "totalCases": 0,
  "approvedCases": 0,
  "observedCases": 0,
  "deniedCases": 0,
  "humanReviewCases": 0,
  "approvalRate": 0,
  "latestAudits": []
}
```

El frontend debe tratar listas vacias y contadores en cero como estados validos, no como errores de conexion.

Respuesta de auditoria:

```json
{
  "caseId": "SIN-2026-004",
  "status": "OBSERVADO",
  "riskScore": 75,
  "summary": "Auditoria completada con hallazgos.",
  "invoiceTotal": 1200,
  "expectedTotal": 950,
  "difference": 250,
  "findings": [],
  "discrepancies": [],
  "topReasons": [],
  "recommendation": "Solicitar sustento adicional."
}
```

## Carga De Documentos

Endpoint:

```http
POST /api/cases/{caseId}/documents
Content-Type: multipart/form-data
```

Campos:

```text
files: uno o varios archivos
documents: JSON serializado con metadata de cada archivo
```

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

La cantidad de items en `documents` debe coincidir con la cantidad de archivos enviados en `files`.

Los archivos se guardan en:

```text
storage/uploads/{caseId}/{documentId}/{filename}
```

Cada documento queda asociado al caso en MongoDB con metadata, texto extraido y estado de parseo.

Estados de parseo:

```text
RECIBIDO
PROCESANDO
PROCESADO
OCR_PENDIENTE
ERROR
```

## Estados Y Enums

Estados de caso:

```text
NUEVO
PENDIENTE_DOCUMENTOS
LISTO_PARA_AUDITORIA
EN_AUDITORIA
OBSERVADO
APROBADO
DENEGADO
REVISION_HUMANA
```

Tipos de documento:

```text
FACTURA
ORDEN_REPARACION
DETALLE_MANO_OBRA
FOTOS_DANIO
TARIFARIO
POLIZA
SUSTENTO_ADICIONAL
```

Roles:

```text
ADMIN
AUDITOR
WORKSHOP
```

Tipos de regla:

```text
PRECIO_MAXIMO
ITEM_DUPLICADO
ITEM_NO_RELACIONADO
CANTIDAD_MAXIMA
DOCUMENTO_OBLIGATORIO
PORCENTAJE_VARIACION
```

Operadores:

```text
MAYOR_QUE
MENOR_QUE
IGUAL_A
DIFERENTE_DE
CONTIENE
NO_CONTIENE
```

Severidades:

```text
BAJA
MEDIA
ALTA
CRITICA
```

## Manejo De Errores

Formato esperado:

```json
{
  "detail": "Mensaje del error."
}
```

Codigos comunes:

```text
401: no autenticado o token invalido
403: sin permisos
404: recurso no encontrado
422: payload invalido
500: error interno
```

## Verificacion

Compilar imports:

```bash
python -m compileall app test_openai.py
```

Revisar dependencias:

```bash
python -m pip check
```

Probar OpenAI:

```bash
python test_openai.py
```

Cargar datos demo:

```bash
python -m app.database.seed_demo
```

Probar API desplegada:

```bash
curl https://demo-hackaithon-backend.onrender.com/health
curl https://demo-hackaithon-backend.onrender.com/api/cases
curl https://demo-hackaithon-backend.onrender.com/api/statistics/dashboard
curl https://demo-hackaithon-backend.onrender.com/api/business-rules
```

## Problemas Comunes

### `ImportError: cannot import name 'StrEnum'`

Estas usando Python 3.10 o menor. Usa Python 3.11+; recomendado Python 3.13.4.

### Render usa Python 3.14

Verifica `.python-version`, `runtime.txt` y la variable:

```env
PYTHON_VERSION=3.13.4
```

Luego ejecuta un deploy con cache limpia.

### Error de `pydantic-core` con Rust o maturin

Ocurre porque Render intenta instalar con Python 3.14 y no encuentra wheel compatible para la version fijada. La solucion es usar Python 3.13.4.

### Error de Passlib con bcrypt

`passlib==1.7.4` debe usarse con:

```text
bcrypt==4.0.1
```

### El frontend no conecta

Revisar:

- `VITE_API_BASE_URL=https://demo-hackaithon-backend.onrender.com/api`
- redeploy del frontend despues de cambiar variables
- `BACKEND_CORS_ORIGINS` en Render
- pestana Network del navegador para ver la URL exacta llamada por React

### MongoDB no conecta

Revisar:

- `MONGODB_URI`
- usuario y password de MongoDB Atlas
- whitelist de IPs en Atlas
- nombre de base de datos en `MONGODB_DB`

## Seguridad

- No versionar `.env`.
- No poner API keys en React.
- Rotar claves expuestas.
- Cambiar `JWT_SECRET_KEY` en produccion.
- Activar `AUTH_REQUIRED=true` cuando el flujo de login ya este conectado.
- Mantener `OPENAI_API_KEY` solo en Render o entorno local.
