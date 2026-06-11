# Documentacion Del Backend AuditIA Para Exposicion Y Deploy En AWS

## 1. Resumen Del Proyecto

AuditIA es un backend REST construido para auditar casos de siniestros vehiculares. Su objetivo es recibir informacion de casos, documentos de soporte, reglas de negocio y ejecutar auditorias que detecten inconsistencias como documentos faltantes, diferencias financieras, items no relacionados con el dano reportado o posibles casos que requieran revision humana.

El backend esta pensado para conectarse con un frontend React/Vite mediante una API HTTP. Tambien puede funcionar de forma independiente porque FastAPI genera automaticamente Swagger, ReDoc y el esquema OpenAPI.

URLs importantes en local:

```text
API base: http://localhost:8000
API con prefijo: http://localhost:8000/api
Swagger: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
OpenAPI JSON: http://localhost:8000/api/openapi.json
Healthcheck: http://localhost:8000/health
```

## 2. Stack Tecnologico

| Capa | Tecnologia | Uso En El Proyecto |
|---|---|---|
| Lenguaje | Python 3.13.4 | Lenguaje principal del backend. |
| Framework API | FastAPI | Creacion de endpoints REST, validacion y Swagger automatico. |
| Servidor ASGI local | Uvicorn | Ejecuta la app en desarrollo. |
| Servidor produccion | Gunicorn + Uvicorn Worker | Ejecuta FastAPI en AWS Elastic Beanstalk. |
| Base de datos | MongoDB / MongoDB Atlas | Persistencia de usuarios, casos, documentos, auditorias y reglas. |
| Driver MongoDB | Motor | Cliente asincrono para MongoDB. |
| ODM | Beanie | Modelos documentales sobre MongoDB. |
| Validacion | Pydantic v2 | Schemas de request/response y validacion de datos. |
| Configuracion | Pydantic Settings | Variables de entorno desde `.env` o entorno cloud. |
| Autenticacion | JWT con python-jose | Tokens Bearer para proteger endpoints. |
| Password hashing | Passlib + bcrypt | Hash seguro de contrasenas. |
| Uploads | python-multipart | Recepcion de archivos por `multipart/form-data`. |
| IA | LangChain + OpenAI SDK | Auditoria asistida por LLM si existe `OPENAI_API_KEY`. |
| Parser documentos | PyPDF2, csv, json, zip/xml | Extraccion de texto desde PDF, JSON, CSV, XLSX y TXT. |
| Calidad/analisis | SonarCloud configurado | Analisis estatico mediante `sonar-project.properties`. |

Dependencias principales declaradas en `requirements.txt`:

```text
fastapi==0.115.6
uvicorn[standard]==0.34.0
gunicorn==23.0.0
beanie==1.28.0
motor==3.6.0
pydantic==2.10.4
pydantic-settings==2.7.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
python-multipart==0.0.20
langchain
langchain-community
langchain-openai
openai==1.66.3
pypdf2==3.0.1
```

## 3. Arquitectura Del Backend

El proyecto esta organizado por dominios:

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
    seed_demo.py
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

Responsabilidades principales:

| Modulo | Responsabilidad |
|---|---|
| `main.py` | Crea FastAPI, CORS, healthcheck, eventos de conexion a MongoDB y registra routers. |
| `core/config.py` | Centraliza variables de entorno como MongoDB, JWT, CORS, OpenAI y uploads. |
| `core/dependencies.py` | Resuelve usuario actual desde `Authorization: Bearer`. |
| `core/security.py` | Hash de contrasenas y generacion/validacion de JWT. |
| `database/mongo.py` | Inicializa Motor, Beanie y modelos documentales. |
| `database/init_db.py` | Crea automaticamente un usuario administrador por defecto si no existe. |
| `auth` | Registro, login y usuario autenticado. |
| `cases` | CRUD principal de casos y carga/listado de documentos. |
| `audits` | Ejecucion de auditorias individuales, por lote, veredicto final e historial. |
| `business_rules` | Reglas parametrizables para validar documentos/casos. |
| `dashboard` | Estadisticas para tablero y razones de denegacion. |
| `shared/ai_service.py` | Integracion opcional con OpenAI mediante LangChain. |
| `shared/file_parser.py` | Extraccion segura de texto desde documentos cargados. |

## 4. Configuracion Y Variables De Entorno

El archivo `.env.example` documenta las variables necesarias. En AWS no se debe subir el `.env`; las variables deben configurarse desde la consola de Elastic Beanstalk o el servicio elegido.

```env
APP_NAME=AuditIA API
ENVIRONMENT=production
API_PREFIX=/api
BACKEND_CORS_ORIGINS=https://tu-frontend.vercel.app,http://localhost:5173

MONGODB_URI=mongodb+srv://usuario:password@cluster.mongodb.net
MONGODB_DB=auditoria_siniestros

AUTH_REQUIRED=false
JWT_SECRET_KEY=usa-un-secreto-largo-y-seguro
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

Notas para explicar:

- `API_PREFIX=/api` hace que los endpoints de negocio queden bajo `/api`.
- `/health` no usa prefijo para que AWS pueda revisar si el servicio esta vivo.
- `AUTH_REQUIRED=false` permite modo demo sin token obligatorio.
- `AUTH_REQUIRED=true` obliga a enviar `Authorization: Bearer <token>`.
- `OPENAI_API_KEY` es opcional; si no existe, la auditoria sigue funcionando con reglas locales.
- `BACKEND_CORS_ORIGINS` debe incluir el dominio real del frontend desplegado.

## 5. Autenticacion Y Seguridad

El backend usa JWT Bearer Token. El flujo normal es:

1. Crear usuario con `POST /api/auth/register` o usar el admin generado por defecto.
2. Iniciar sesion con `POST /api/auth/login`.
3. Recibir `accessToken`.
4. Enviar el token en endpoints protegidos:

```http
Authorization: Bearer <accessToken>
```

En modo demo, si `AUTH_REQUIRED=false`, los endpoints protegidos permiten peticiones sin token. Esto facilita la presentacion y pruebas, pero en produccion real se recomienda activar `AUTH_REQUIRED=true`.

Medidas de seguridad existentes:

- Hash de contrasenas con Passlib + bcrypt.
- JWT firmado con `JWT_SECRET_KEY`.
- CORS restringible por variable de entorno.
- Validacion automatica de payloads con Pydantic.
- Limite de tamano total para uploads.
- Lista de extensiones permitidas para documentos.
- Sanitizacion basica de nombres de archivo.
- No se deben versionar claves reales en Git.

## 6. Convenciones De La API

- La API responde en JSON.
- Los modelos internos usan `snake_case`, pero las respuestas y requests soportan `camelCase` gracias al alias generator de Pydantic.
- Ejemplo: internamente `claim_number`, externamente `claimNumber`.
- Los estados y tipos se manejan con enums para evitar valores inconsistentes.
- Los errores comunes responden con el formato de FastAPI:

```json
{
  "detail": "Mensaje del error."
}
```

Codigos frecuentes:

| Codigo | Significado |
|---|---|
| 200 | Operacion correcta. |
| 201 | Recurso creado. |
| 204 | Recurso eliminado sin cuerpo de respuesta. |
| 401 | No autenticado o token invalido. |
| 403 | Sin permisos. |
| 404 | Recurso no encontrado. |
| 409 | Conflicto, por ejemplo caso duplicado. |
| 413 | Upload supera el limite permitido. |
| 422 | Payload invalido. |
| 500 | Error interno. |

## 7. Endpoints De Salud Y Documentacion

### GET `/health`

Verifica que la API esta viva. Es el endpoint recomendado para healthcheck en AWS.

Respuesta:

```json
{
  "status": "ok",
  "environment": "production"
}
```

### GET `/docs`

Abre Swagger UI generado automaticamente por FastAPI.

### GET `/redoc`

Abre ReDoc, otra vista de documentacion OpenAPI.

### GET `/api/openapi.json`

Devuelve el contrato OpenAPI en JSON.

## 8. Endpoints De Autenticacion

### POST `/api/auth/register`

Crea un usuario nuevo.

Request:

```json
{
  "email": "auditor@example.com",
  "fullName": "Auditor Demo",
  "password": "password123",
  "role": "AUDITOR"
}
```

Respuesta `201`:

```json
{
  "id": "665f...",
  "email": "auditor@example.com",
  "fullName": "Auditor Demo",
  "role": "AUDITOR",
  "isActive": true
}
```

### POST `/api/auth/login`

Autentica un usuario y devuelve un token JWT.

Request:

```json
{
  "email": "admin@example.com",
  "password": "change-me"
}
```

Respuesta:

```json
{
  "accessToken": "token.jwt...",
  "tokenType": "bearer",
  "user": {
    "id": "665f...",
    "email": "admin@example.com",
    "fullName": "AuditIA Admin",
    "role": "ADMIN",
    "isActive": true
  }
}
```

### GET `/api/auth/me`

Devuelve el usuario actual segun el token. En modo demo sin token devuelve un usuario ficticio de desarrollo.

Header recomendado:

```http
Authorization: Bearer <accessToken>
```

## 9. Endpoints De Casos

Los casos representan siniestros vehiculares que se van a auditar.

### GET `/api/cases`

Lista todos los casos registrados.

Respuesta:

```json
{
  "cases": [
    {
      "id": "665f...",
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
      "status": "NUEVO",
      "confidence": null,
      "findings": [],
      "receivedAt": null,
      "createdAt": "2026-06-11T00:00:00Z",
      "updatedAt": "2026-06-11T00:00:00Z"
    }
  ]
}
```

### POST `/api/cases`

Crea un caso nuevo.

Request:

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

Respuesta `201`: objeto del caso creado.

Validaciones importantes:

- `claimNumber` es obligatorio y no debe repetirse.
- `status` debe ser un valor valido del enum de estados.
- `invoiceTotal` y `tariffTotal` son opcionales, pero ayudan a detectar diferencias financieras.

### GET `/api/cases/documents`

Lista todos los documentos cargados, sin filtrar por caso.

Respuesta:

```json
{
  "caseId": null,
  "documents": []
}
```

### GET `/api/cases/{caseId}`

Obtiene un caso por `claimNumber` o por ID interno de MongoDB.

Ejemplo:

```http
GET /api/cases/SIN-2026-001
```

### PATCH `/api/cases/{caseId}/status`

Actualiza manualmente el estado de un caso.

Request:

```json
{
  "status": "LISTO_PARA_AUDITORIA"
}
```

Respuesta: caso actualizado.

### GET `/api/cases/{caseId}/documents`

Lista documentos asociados a un caso especifico.

Respuesta:

```json
{
  "caseId": "SIN-2026-001",
  "documents": [
    {
      "id": "665f...",
      "caseId": "SIN-2026-001",
      "documentType": "FACTURA",
      "type": "FACTURA",
      "name": "factura.pdf",
      "originalName": "factura.pdf",
      "size": 123456,
      "extension": "pdf",
      "mimeType": "application/pdf",
      "uploadedAt": "2026-06-11T00:00:00Z",
      "status": "RECIBIDO",
      "parseStatus": "PROCESADO",
      "parseError": null,
      "extractionStatus": "PROCESADO"
    }
  ]
}
```

### POST `/api/cases/{caseId}/documents`

Carga uno o varios documentos asociados a un caso. Usa `multipart/form-data`.

Campos:

| Campo | Tipo | Descripcion |
|---|---|---|
| `files` | archivo/lista | Archivos reales. |
| `documents` | string JSON | Metadata serializada de cada archivo. |

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

Reglas:

- La cantidad de archivos debe coincidir con la cantidad de items en `documents`.
- Extensiones permitidas: `pdf`, `csv`, `xlsx`, `json`, `png`, `jpg`, `jpeg`, `txt`.
- Las imagenes quedan con `OCR_PENDIENTE` porque el proyecto no ejecuta OCR local.
- PDF, CSV, JSON, XLSX y TXT intentan extraer texto.
- Al cargar documentos, el caso pasa a `LISTO_PARA_AUDITORIA`.
- Los archivos se guardan en `storage/uploads/{claimNumber}/{documentId}/{filename}`.

## 10. Endpoints De Auditorias

Las auditorias analizan un caso usando documentos, reglas de negocio, validaciones financieras y, opcionalmente, OpenAI.

### POST `/api/audit/{caseId}`

Ejecuta una auditoria individual para un caso.

Request opcional:

```json
{
  "caseId": "SIN-2026-001",
  "vehicle": {},
  "reportedDamages": [],
  "documents": [],
  "requestedBy": "profesor-demo",
  "source": "manual"
}
```

Respuesta:

```json
{
  "auditId": "AUD-ABC1234567",
  "caseId": "SIN-2026-001",
  "status": "OBSERVADO",
  "riskScore": 35,
  "confidence": 0.65,
  "summary": "Auditoria completada con 2 hallazgo(s).",
  "invoiceTotal": 1200,
  "expectedTotal": 1100,
  "difference": 100,
  "findings": [],
  "discrepancies": [],
  "topReasons": [],
  "recommendation": "Solicitar sustento adicional y revisar discrepancias.",
  "documents": [],
  "finalVerdict": null,
  "createdAt": "2026-06-11T00:00:00Z"
}
```

Logica principal:

- Cambia el caso a `EN_AUDITORIA` mientras procesa.
- Revisa documentos obligatorios.
- Evalua reglas de negocio activas.
- Calcula diferencia entre `invoiceTotal` y `tariffTotal`.
- Busca consistencia entre danos reportados y texto extraido.
- Si hay `OPENAI_API_KEY`, agrega analisis del LLM.
- Guarda la auditoria en MongoDB.
- Actualiza el estado final del caso.

### POST `/api/audit/batch`

Ejecuta auditoria para varios casos, maximo 5 por request.

Request:

```json
{
  "caseIds": ["SIN-2026-001", "SIN-2026-002"]
}
```

Respuesta:

```json
{
  "audits": []
}
```

### POST `/api/audit/{caseId}/final-verdict`

Ejecuta una auditoria marcada como veredicto final. Devuelve el mismo contrato de auditoria, pero con `finalVerdict` diligenciado.

### GET `/api/audit/{caseId}/latest`

Devuelve la auditoria mas reciente de un caso.

### GET `/api/audit/{caseId}/history`

Devuelve el historial de auditorias de un caso.

Respuesta:

```json
{
  "history": []
}
```

### GET `/api/audit/history`

Devuelve el historial global de auditorias de todos los casos.

## 11. Endpoints De Reglas De Negocio

Las reglas permiten configurar validaciones sin cambiar codigo. Por ejemplo: documento obligatorio, precio maximo o porcentaje de variacion.

### GET `/api/business-rules`

Lista reglas existentes.

Respuesta:

```json
{
  "rules": []
}
```

### POST `/api/business-rules`

Crea una regla.

Request:

```json
{
  "name": "Factura obligatoria",
  "description": "Todo caso debe incluir factura.",
  "type": "DOCUMENTO_OBLIGATORIO",
  "targetField": "documents",
  "operator": "CONTIENE",
  "referenceValue": "FACTURA",
  "severity": "ALTA",
  "status": "ACTIVA",
  "alertMessage": "Falta la factura del caso."
}
```

Respuesta `201`: regla creada.

### PUT `/api/business-rules/{ruleId}`

Actualiza una regla completa.

### PATCH `/api/business-rules/{ruleId}/toggle`

Activa o desactiva una regla. Si esta `ACTIVA`, pasa a `INACTIVA`; si esta `INACTIVA`, pasa a `ACTIVA`.

### DELETE `/api/business-rules/{ruleId}`

Elimina una regla. Responde `204 No Content`.

## 12. Endpoints De Estadisticas

### GET `/api/statistics/dashboard`

Devuelve metricas para el dashboard.

Respuesta:

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

### GET `/api/statistics/denial-reasons`

Devuelve razones principales de denegacion u observacion segun auditorias.

Respuesta:

```json
{
  "reasons": [
    {
      "reason": "La factura supera el valor esperado por tarifario.",
      "count": 3,
      "percentage": 60
    }
  ]
}
```

## 13. Enums Principales

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

Estados de parseo:

```text
RECIBIDO
PROCESANDO
PROCESADO
OCR_PENDIENTE
ERROR
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

Estados de regla:

```text
ACTIVA
INACTIVA
```

## 14. Como Funciona La Auditoria

El proceso de auditoria combina reglas deterministicas con IA opcional:

1. Busca el caso por `claimNumber` o ID.
2. Consulta documentos relacionados en MongoDB.
3. Consulta reglas de negocio activas.
4. Evalua documentos obligatorios base: factura, orden de reparacion, detalle de mano de obra y fotos del dano.
5. Si existe `tariffTotal`, tambien exige tarifario.
6. Revisa errores de parseo u OCR pendiente.
7. Evalua reglas de tipo `DOCUMENTO_OBLIGATORIO`.
8. Calcula diferencia financiera entre factura y tarifario.
9. Revisa si los danos reportados aparecen en el texto extraido.
10. Si hay OpenAI configurado, envia contexto controlado para detectar discrepancias adicionales.
11. Calcula `riskScore` segun severidad de hallazgos.
12. Define estado final: `APROBADO`, `OBSERVADO`, `DENEGADO` o `REVISION_HUMANA`.
13. Guarda auditoria y actualiza el caso.

Escala de riesgo local:

| Severidad | Peso |
|---|---:|
| BAJA | 5 |
| MEDIA | 10 |
| ALTA | 18 |
| CRITICA | 35 |

Decision de estado:

- Si hay discrepancia critica financiera, cobertura o precio maximo, puede quedar `DENEGADO`.
- Si el riesgo es mayor o igual a 70, queda `REVISION_HUMANA`.
- Si hay discrepancias no criticas, queda `OBSERVADO`.
- Si no hay discrepancias, queda `APROBADO`.

## 15. Persistencia En MongoDB

Colecciones principales manejadas por Beanie:

| Modelo | Contenido |
|---|---|
| `User` | Usuarios, email, hash de password, rol y estado. |
| `Case` | Siniestros, vehiculo, valores financieros, estado y hallazgos. |
| `CaseDocument` | Metadata del documento, ruta local, texto extraido y estado de parseo. |
| `Audit` | Resultado de auditorias, riesgo, hallazgos, discrepancias y recomendacion. |
| `BusinessRule` | Reglas configurables y estado activo/inactivo. |

En AWS se recomienda usar MongoDB Atlas como base administrada, porque Elastic Beanstalk no incluye MongoDB por defecto.

## 16. Deploy En AWS Elastic Beanstalk

Elastic Beanstalk es la opcion mas directa para este proyecto porque el repositorio ya incluye `Procfile`, `runtime.txt`, `.python-version`, `.ebignore` y `requirements.txt`.

### 16.1 Archivos Preparados Para AWS

`runtime.txt`:

```text
python-3.13.4
```

`Procfile`:

```text
web: gunicorn app.main:app --bind :8000 --workers 2 --worker-class uvicorn.workers.UvicornWorker --timeout 120
```

Explicacion del `Procfile`:

- `gunicorn` es el servidor de produccion.
- `app.main:app` apunta al objeto FastAPI creado en `app/main.py`.
- `--bind :8000` escucha en el puerto esperado por la plataforma.
- `--worker-class uvicorn.workers.UvicornWorker` permite ejecutar la app ASGI de FastAPI.
- `--workers 2` levanta dos procesos para manejar peticiones.
- `--timeout 120` da mas tiempo para auditorias o uploads.

### 16.2 Configuracion Recomendada En Elastic Beanstalk

Crear aplicacion con:

```text
Platform: Python
Platform branch: Python 3.13 running on 64bit Amazon Linux 2023
Environment type: Single instance para demo, Load balanced para produccion
Health check path: /health
```

Variables de entorno en Beanstalk:

```env
ENVIRONMENT=production
API_PREFIX=/api
BACKEND_CORS_ORIGINS=https://tu-frontend.vercel.app,http://localhost:5173
MONGODB_URI=mongodb+srv://usuario:password@cluster.mongodb.net
MONGODB_DB=auditoria_siniestros
AUTH_REQUIRED=false
JWT_SECRET_KEY=usa-un-secreto-largo-y-seguro
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
UPLOAD_MAX_TOTAL_BYTES=20971520
UPLOAD_ALLOWED_EXTENSIONS=pdf,csv,xlsx,json,png,jpg,jpeg,txt
UPLOAD_LOCAL_DIR=storage/uploads
DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=change-me
DEFAULT_ADMIN_FULL_NAME=AuditIA Admin
OPENAI_API_KEY=tu_api_key_si_usas_ia
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.1
```

### 16.3 Pasos Manuales Con ZIP

1. Crear un cluster en MongoDB Atlas.
2. Configurar usuario, password y whitelist de IPs en Atlas.
3. Crear aplicacion en Elastic Beanstalk con plataforma Python.
4. Configurar variables de entorno en Beanstalk.
5. Comprimir desde la raiz del repositorio.
6. El ZIP debe contener directamente `app/`, `requirements.txt`, `Procfile`, `runtime.txt` y no una carpeta contenedora.
7. Subir el ZIP en Elastic Beanstalk.
8. Configurar healthcheck en `/health`.
9. Probar `https://tu-dominio.elasticbeanstalk.com/health`.
10. Probar Swagger en `https://tu-dominio.elasticbeanstalk.com/docs`.

### 16.4 Deploy Automatico Con GitHub Actions

El README indica que puede existir un workflow para desplegar a Elastic Beanstalk cuando SonarCloud termina correctamente en `main`.

Secrets requeridos en GitHub:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
```

Variables requeridas en GitHub:

```text
AWS_REGION=us-east-1
EB_APPLICATION_NAME=nombre-de-tu-aplicacion
EB_ENVIRONMENT_NAME=nombre-de-tu-entorno
EB_S3_BUCKET=nombre-del-bucket-para-versiones
```

Funcionamiento esperado:

- GitHub Actions crea un ZIP desde el repositorio.
- Lo sube a S3.
- Crea una version de aplicacion en Elastic Beanstalk.
- Actualiza el environment con esa version.

## 17. Consideraciones AWS Importantes

### Base De Datos

Elastic Beanstalk ejecuta el backend, pero no provee MongoDB. Se recomienda MongoDB Atlas.

En Atlas revisar:

- Usuario y password correctos.
- String `MONGODB_URI` valido.
- IP permitida. Para una demo se puede permitir temporalmente `0.0.0.0/0`, pero no es lo ideal para produccion.
- Nombre de base de datos en `MONGODB_DB`.

### Archivos Subidos

Actualmente los documentos se guardan en disco local bajo `storage/uploads`. Para demo funciona, pero en produccion con instancias reemplazables o escalamiento horizontal se recomienda migrar uploads a Amazon S3.

Riesgo actual:

- Si AWS reemplaza la instancia, los archivos locales pueden perderse.
- Si hay varias instancias, cada una tendra archivos distintos.

Mejora futura recomendada:

- Guardar archivos en S3.
- Guardar en MongoDB solo metadata y URL/key de S3.

### CORS

Si el frontend esta en Vercel, Netlify o S3/CloudFront, agregar ese dominio exacto en `BACKEND_CORS_ORIGINS`.

Ejemplo:

```env
BACKEND_CORS_ORIGINS=https://auditia-frontend.vercel.app
```

### Secretos

No guardar en Git:

- `.env`
- `MONGODB_URI` real
- `JWT_SECRET_KEY` real
- `OPENAI_API_KEY`
- credenciales AWS

### Healthcheck

AWS debe revisar:

```text
/health
```

No usar `/api/health` porque ese endpoint no existe.

## 18. Comandos Locales

Crear entorno:

```bash
py -3.13 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

Ejecutar API:

```bash
python -m uvicorn app.main:app --reload
```

Ejecutar con host visible en red local:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Cargar datos demo:

```bash
python -m app.database.seed_demo
```

Verificar imports:

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

## 19. Pruebas Rapidas Con Curl

Healthcheck:

```bash
curl http://localhost:8000/health
```

Listar casos:

```bash
curl http://localhost:8000/api/cases
```

Crear caso:

```bash
curl -X POST http://localhost:8000/api/cases ^
  -H "Content-Type: application/json" ^
  -d "{\"claimNumber\":\"SIN-2026-001\",\"workshop\":\"Taller Central\",\"vehicle\":{\"brand\":\"Toyota\",\"model\":\"Corolla\",\"year\":2020},\"plate\":\"ABC-1234\",\"reportedDamages\":[\"parachoques\"],\"invoiceTotal\":1200,\"tariffTotal\":1100,\"status\":\"NUEVO\"}"
```

Ejecutar auditoria:

```bash
curl -X POST http://localhost:8000/api/audit/SIN-2026-001 ^
  -H "Content-Type: application/json" ^
  -d "{\"source\":\"manual\"}"
```

Dashboard:

```bash
curl http://localhost:8000/api/statistics/dashboard
```

## 20. Guion Corto Para Explicarle Al Profesor

Este backend se llama AuditIA y esta construido con FastAPI y MongoDB. La API permite registrar casos de siniestros vehiculares, cargar documentos como facturas, ordenes de reparacion, fotos, tarifarios o polizas, definir reglas de negocio y ejecutar auditorias automaticas.

La auditoria combina validaciones programadas con IA opcional. Primero revisa documentos obligatorios, diferencias entre factura y tarifario, reglas activas y consistencia del texto extraido. Si se configura OpenAI, tambien se envia un contexto controlado para recibir hallazgos adicionales. El resultado queda guardado como una auditoria con puntaje de riesgo, estado, hallazgos, discrepancias y recomendacion.

El backend esta preparado para AWS Elastic Beanstalk porque incluye `Procfile`, `runtime.txt`, `.ebignore` y dependencias en `requirements.txt`. En produccion se recomienda usar MongoDB Atlas como base de datos y configurar las credenciales como variables de entorno en AWS, no dentro del codigo.

El endpoint `/health` sirve para que AWS verifique que la aplicacion esta funcionando. Los endpoints principales estan bajo `/api`, por ejemplo `/api/cases`, `/api/audit/{caseId}`, `/api/business-rules` y `/api/statistics/dashboard`. FastAPI tambien genera documentacion automatica en `/docs`, lo que facilita probar y explicar cada endpoint.

## 21. Recomendaciones Futuras

- Activar `AUTH_REQUIRED=true` cuando el frontend maneje login completamente.
- Migrar almacenamiento local de documentos a Amazon S3.
- Usar CloudWatch para logs y monitoreo en AWS.
- Configurar HTTPS con dominio propio o Load Balancer.
- Restringir IPs de MongoDB Atlas para produccion.
- Agregar pruebas automatizadas de endpoints criticos.
- Separar ambientes `development`, `staging` y `production`.
