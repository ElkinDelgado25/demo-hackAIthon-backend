# SecureMAX Backend

Backend API REST desarrollado con el framework **FastAPI** para SecureMAX, un sistema de apoyo para aseguradoras que permite registrar casos de siniestros vehiculares, cargar documentos, aplicar reglas de negocio y ejecutar auditorias asistidas por IA.

El proyecto expone una API lista para conectarse con un frontend React/Vite y tambien puede probarse directamente desde Swagger.

## Descripcion corta para GitHub

```text
Backend API REST con FastAPI, MongoDB e IA para auditoria inteligente de siniestros vehiculares.
```

## Que Hace SecureMAX

SecureMAX ayuda a revisar casos de siniestros vehiculares de forma mas ordenada y trazable. El backend centraliza la informacion del caso, los documentos cargados, las reglas de negocio y los resultados de auditoria para detectar posibles inconsistencias antes de aprobar, observar o derivar un caso a revision humana.

El sistema esta pensado para:

- registrar casos de siniestros vehiculares;
- guardar informacion del vehiculo, taller, danos reportados y valores de factura;
- cargar documentos como facturas, ordenes de reparacion, fotos, polizas o tarifarios;
- extraer texto basico desde archivos PDF, CSV, XLSX, JSON y TXT;
- ejecutar reglas de negocio configurables;
- generar auditorias con hallazgos, discrepancias, puntaje de riesgo y recomendacion;
- consultar estadisticas para un dashboard;
- proteger endpoints con autenticacion JWT cuando el modo seguro este activo.

## Stack Tecnico

| Capa | Tecnologia | Uso |
|---|---|---|
| Lenguaje | Python 3.13.4 | Lenguaje principal del backend |
| Framework | FastAPI | Construccion de API REST, Swagger y validacion |
| Servidor local | Uvicorn | Ejecucion en desarrollo |
| Servidor produccion | Gunicorn + Uvicorn Worker | Ejecucion en AWS Elastic Beanstalk |
| Base de datos | MongoDB / MongoDB Atlas | Persistencia de usuarios, casos, documentos, auditorias y reglas |
| ODM | Beanie | Modelos documentales sobre MongoDB |
| Driver MongoDB | Motor | Cliente asincrono para MongoDB |
| Validacion | Pydantic v2 | Schemas de entrada y salida |
| Configuracion | Pydantic Settings | Variables de entorno desde `.env` |
| Autenticacion | python-jose + JWT | Tokens Bearer |
| Seguridad password | Passlib + bcrypt | Hash de contrasenas |
| IA | LangChain + OpenAI SDK | Auditoria asistida por LLM |
| Archivos | python-multipart + PyPDF2 | Carga y lectura basica de documentos |

## Arquitectura Del Proyecto

```text
app/
  main.py                  # Crea la app FastAPI y registra routers
  core/                    # Configuracion, seguridad, dependencias y errores
  database/                # Conexion e inicializacion de MongoDB
  auth/                    # Registro, login y usuario actual
  users/                   # Modelos y schemas de usuarios
  cases/                   # Casos, documentos y estados
  audits/                  # Ejecucion e historial de auditorias
  business_rules/          # Reglas de negocio configurables
  dashboard/               # Estadisticas para panel principal
  shared/                  # IA, enums, parsers y schemas compartidos
```

## Requisitos

- Python 3.13.4
- MongoDB local o MongoDB Atlas
- Cuenta/API key de OpenAI si se desea usar auditoria con IA
- Frontend opcional apuntando a la URL base del backend

## Instalacion Local

Desde la carpeta del backend:

```bash
py -3.13 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
```

Luego ajusta el archivo `.env` con tu conexion a MongoDB y tus variables reales.

Ejecutar el servidor:

```bash
python -m uvicorn app.main:app --reload
```

URLs locales:

| Servicio | URL |
|---|---|
| API base | `http://localhost:8000` |
| API con prefijo | `http://localhost:8000/api` |
| Swagger | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |
| OpenAPI JSON | `http://localhost:8000/api/openapi.json` |
| Healthcheck | `http://localhost:8000/health` |

## Variables De Entorno

El proyecto usa `.env` para configuracion local. Puedes partir desde `.env.example`.

Ejemplo:

```env
APP_NAME=SecureMAX API
ENVIRONMENT=development
API_PREFIX=/api
BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=securemax_siniestros

AUTH_REQUIRED=false
JWT_SECRET_KEY=change-me-use-a-long-random-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

UPLOAD_MAX_TOTAL_BYTES=20971520
UPLOAD_ALLOWED_EXTENSIONS=pdf,csv,xlsx,json,png,jpg,jpeg,txt
UPLOAD_LOCAL_DIR=storage/uploads

DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=change-me
DEFAULT_ADMIN_FULL_NAME=SecureMAX Admin

OPENAI_API_KEY=
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.1
CHROMA_COLLECTION=securemax_documents
```

No subas claves reales al repositorio. Las credenciales de MongoDB, OpenAI, JWT y AWS deben configurarse como variables de entorno o secrets.

## Endpoints Principales

### Salud

```text
GET /health
```

### Autenticacion

```text
POST /api/auth/register
POST /api/auth/login
GET /api/auth/me
```

Cuando `AUTH_REQUIRED=true`, los endpoints protegidos requieren:

```http
Authorization: Bearer <accessToken>
```

Para demo o desarrollo puede mantenerse:

```env
AUTH_REQUIRED=false
```

### Casos

```text
GET /api/cases
POST /api/cases
GET /api/cases/{caseId}
PATCH /api/cases/{caseId}/status
GET /api/cases/documents
GET /api/cases/{caseId}/documents
POST /api/cases/{caseId}/documents
```

Ejemplo para crear un caso:

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

### Auditorias

```text
POST /api/audit/batch
GET /api/audit/history
POST /api/audit/{caseId}
POST /api/audit/{caseId}/final-verdict
GET /api/audit/{caseId}/latest
GET /api/audit/{caseId}/history
```

Respuesta esperada de auditoria:

```json
{
  "caseId": "SIN-2026-001",
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

### Reglas De Negocio

```text
GET /api/business-rules
POST /api/business-rules
PUT /api/business-rules/{ruleId}
PATCH /api/business-rules/{ruleId}/toggle
DELETE /api/business-rules/{ruleId}
```

### Estadisticas

```text
GET /api/statistics/dashboard
GET /api/statistics/denial-reasons
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
documents: JSON serializado con la metadata de cada archivo
```

Ejemplo de metadata:

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

La cantidad de objetos en `documents` debe coincidir con la cantidad de archivos enviados en `files`.

Los archivos se almacenan localmente en:

```text
storage/uploads/{caseId}/{documentId}/{filename}
```

## Estados Y Catalogos

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

## Integracion Con Frontend

El frontend debe apuntar al backend usando una URL base que incluya `/api`.

Local:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

Produccion:

```env
VITE_API_BASE_URL=https://demo-hackaithon-backend.onrender.com/api
```

El healthcheck no usa `/api`:

```text
GET /health
```

El frontend no debe guardar credenciales de MongoDB, OpenAI, JWT ni AWS. Esos secretos pertenecen al backend.

## Deploy

### Render

El proyecto fija Python 3.13.4 con:

```text
.python-version
runtime.txt
```

Configuracion recomendada:

```bash
Build Command: pip install -r requirements.txt
Start Command: python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Si Render intenta usar otra version:

```env
PYTHON_VERSION=3.13.4
```

### AWS Elastic Beanstalk

El repositorio incluye:

- `Procfile` para iniciar FastAPI con Gunicorn + Uvicorn Worker.
- `.ebignore` para excluir entornos virtuales, caches y archivos locales.
- `requirements.txt` con dependencias de produccion.

Configuracion recomendada:

```text
Platform: Python 3.13 running on 64bit Amazon Linux 2023
Health check path: /health
Environment type: Single instance para pruebas, Load balanced para produccion
```

Variables importantes en Beanstalk:

```env
ENVIRONMENT=production
API_PREFIX=/api
BACKEND_CORS_ORIGINS=https://tu-frontend.vercel.app,http://localhost:5173
MONGODB_URI=mongodb+srv://usuario:password@cluster.mongodb.net
MONGODB_DB=securemax_siniestros
JWT_SECRET_KEY=usa-un-secreto-largo
AUTH_REQUIRED=false
OPENAI_API_KEY=tu_api_key_si_usas_ia
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.1
UPLOAD_LOCAL_DIR=storage/uploads
```

Si subes un `.zip` manualmente, comprimelo desde la raiz del repositorio. El zip debe contener directamente `app/`, `requirements.txt` y `Procfile`.

## Verificacion

Compilar imports:

```bash
python -m compileall app test_openai.py
```

Revisar dependencias:

```bash
python -m pip check
```

Cargar datos demo:

```bash
python -m app.database.seed_demo
```

Probar healthcheck:

```bash
curl http://localhost:8000/health
```

## Problemas Comunes

### El frontend no conecta

Revisar:

- que el backend este ejecutandose;
- que `VITE_API_BASE_URL` incluya `/api`;
- que `BACKEND_CORS_ORIGINS` incluya el dominio real del frontend;
- la pestana Network del navegador para confirmar que URL esta llamando React.

### MongoDB no conecta

Revisar:

- `MONGODB_URI`;
- usuario y password de MongoDB Atlas;
- whitelist de IPs en Atlas;
- nombre de base de datos en `MONGODB_DB`.

### Error de Python o pydantic-core

Usa Python 3.13.4. Evita Python 3.14 si las dependencias fijadas aun no tienen wheels compatibles.

### Error de Passlib con bcrypt

Este proyecto usa:

```text
passlib==1.7.4
bcrypt==4.0.1
```

## Seguridad

- No versionar `.env`.
- No poner API keys en el frontend.
- Cambiar `JWT_SECRET_KEY` en produccion.
- Rotar inmediatamente cualquier clave expuesta.
- Mantener `OPENAI_API_KEY` solo en el backend.
- Activar `AUTH_REQUIRED=true` cuando el flujo de autenticacion este listo para produccion.

## Calidad

El repositorio tiene configuracion para analisis estatico con SonarCloud mediante `sonar-project.properties` y workflow de GitHub Actions.

Comando local util:

```bash
python -m compileall app test_openai.py
```
