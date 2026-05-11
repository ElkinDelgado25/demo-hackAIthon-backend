# Guia para conectar el frontend con este backend

Este documento resume lo que el frontend React necesita saber para consumir correctamente la API FastAPI.

## URL base

Backend desplegado:

```env
VITE_API_BASE_URL=https://demo-hackaithon-backend.onrender.com/api
```

Backend local:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

La URL debe incluir el prefijo `/api`. El endpoint de salud no usa ese prefijo.

```text
GET https://demo-hackaithon-backend.onrender.com/health
GET https://demo-hackaithon-backend.onrender.com/docs
GET https://demo-hackaithon-backend.onrender.com/api/openapi.json
```

## Regla importante de nombres

El backend esta escrito en Python con campos internos `snake_case`, pero la API usa alias `camelCase` para integrarse mejor con React.

Ejemplo:

```json
{
  "claimNumber": "SIN-2026-001",
  "reportedDamages": ["capot", "parachoques"],
  "invoiceTotal": 1200,
  "tariffTotal": 1100
}
```

El backend tambien acepta `snake_case` por compatibilidad, pero el frontend deberia usar `camelCase`.

## Autenticacion

Endpoints publicos:

```text
POST /api/auth/register
POST /api/auth/login
GET /health
GET /docs
GET /api/openapi.json
```

Login:

```http
POST /api/auth/login
Content-Type: application/json
```

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

Cuando `AUTH_REQUIRED=true`, el frontend debe enviar el token en rutas protegidas:

```http
Authorization: Bearer <accessToken>
```

Si `AUTH_REQUIRED=false`, el backend permite uso sin token para desarrollo o demos.

## Endpoints que consume el frontend

### Casos

```text
GET /api/cases
POST /api/cases
GET /api/cases/{caseId}
PATCH /api/cases/{caseId}/status
GET /api/cases/{caseId}/documents
POST /api/cases/{caseId}/documents
```

Crear caso:

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

Estados validos:

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

Actualizar estado:

```http
PATCH /api/cases/{caseId}/status
Content-Type: application/json
```

```json
{
  "status": "APROBADO"
}
```

Subir documentos:

```http
POST /api/cases/{caseId}/documents
Content-Type: multipart/form-data
```

Campos esperados:

```text
files: uno o varios archivos
documents: JSON string con la metadata de cada archivo
```

Ejemplo del campo `documents`:

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

La cantidad de items en `documents` debe coincidir con la cantidad de archivos en `files`.

Ejemplo con JavaScript:

```js
const formData = new FormData();

files.forEach((file) => {
  formData.append("files", file);
});

formData.append(
  "documents",
  JSON.stringify(
    files.map((file) => ({
      name: file.name,
      type: "FACTURA",
      size: file.size,
      mimeType: file.type || "application/octet-stream"
    }))
  )
);

await fetch(`${apiBaseUrl}/cases/${caseId}/documents`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${token}`
  },
  body: formData
});
```

Tipos de documento validos:

```text
FACTURA
ORDEN_REPARACION
DETALLE_MANO_OBRA
FOTOS_DANIO
```

### Auditorias

```text
POST /api/audit/{caseId}
GET /api/audit/{caseId}/latest
GET /api/audit/{caseId}/history
```

Ejecutar auditoria:

```json
{
  "caseId": "SIN-2026-001",
  "vehicle": {
    "brand": "Toyota",
    "model": "Corolla"
  },
  "reportedDamages": ["parachoques"],
  "documents": [],
  "requestedBy": "frontend",
  "source": "dashboard"
}
```

Respuesta:

```json
{
  "auditId": "...",
  "caseId": "...",
  "status": "OBSERVADO",
  "confidence": 0.75,
  "summary": "Resultado de auditoria.",
  "discrepancies": [],
  "recommendation": "Revisar documentacion.",
  "documents": [],
  "createdAt": "2026-05-11T00:00:00Z"
}
```

### Reglas de negocio

```text
GET /api/business-rules
POST /api/business-rules
PUT /api/business-rules/{ruleId}
PATCH /api/business-rules/{ruleId}/toggle
DELETE /api/business-rules/{ruleId}
```

Crear regla:

```json
{
  "name": "Factura mayor al tarifario",
  "description": "Detecta valores de factura superiores al tarifario permitido.",
  "type": "PRECIO_MAXIMO",
  "targetField": "invoiceTotal",
  "operator": "MAYOR_QUE",
  "referenceValue": "tariffTotal",
  "severity": "ALTA",
  "status": "ACTIVA",
  "alertMessage": "La factura supera el valor permitido."
}
```

Valores validos:

```text
type: PRECIO_MAXIMO | ITEM_DUPLICADO | ITEM_NO_RELACIONADO | CANTIDAD_MAXIMA | DOCUMENTO_OBLIGATORIO | PORCENTAJE_VARIACION
operator: MAYOR_QUE | MENOR_QUE | IGUAL_A | DIFERENTE_DE | CONTIENE | NO_CONTIENE
severity: BAJA | MEDIA | ALTA | CRITICA
status: ACTIVA | INACTIVA
```

Respuesta de listado:

```json
{
  "rules": []
}
```

### Estadisticas

```text
GET /api/statistics/dashboard
GET /api/statistics/denial-reasons
```

Respuesta del dashboard cuando no hay datos:

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

Razones de negacion:

```json
{
  "reasons": []
}
```

## Manejo de estados vacios

El frontend debe considerar estas respuestas como validas, no como errores de conexion:

```json
{ "cases": [] }
{ "rules": [] }
{ "latestAudits": [] }
{ "reasons": [] }
```

Si MongoDB esta conectado pero no hay registros, el backend devuelve listas vacias y contadores en `0`.

## Manejo de errores

Errores esperados:

```json
{
  "detail": "Mensaje del error."
}
```

El frontend deberia manejar:

```text
401: usuario no autenticado o token invalido
403: usuario sin permisos, si se agregan roles mas estrictos
404: recurso no encontrado
422: payload invalido o campos faltantes
500: error interno del backend
```

## CORS

El backend debe tener configurado el dominio del frontend en `BACKEND_CORS_ORIGINS`.

Para Vercel:

```env
BACKEND_CORS_ORIGINS=https://demo-hack-a-ithon-frontend.vercel.app
```

Si el dominio de Vercel cambia, tambien debe actualizarse esta variable en Render.

## Checklist para el frontend

- Definir `VITE_API_BASE_URL=https://demo-hackaithon-backend.onrender.com/api`.
- Redeployar el frontend despues de cambiar variables en Vercel.
- Usar `camelCase` en payloads y lecturas.
- Enviar `Authorization: Bearer <token>` cuando `AUTH_REQUIRED=true`.
- Tratar listas vacias y contadores en cero como estado valido.
- No guardar credenciales de MongoDB ni OpenAI en React.
- No llamar a MongoDB desde el frontend.
- Consultar `/docs` para revisar el contrato OpenAPI actualizado.

## Pruebas rapidas

```bash
curl https://demo-hackaithon-backend.onrender.com/health
curl https://demo-hackaithon-backend.onrender.com/api/cases
curl https://demo-hackaithon-backend.onrender.com/api/statistics/dashboard
curl https://demo-hackaithon-backend.onrender.com/api/business-rules
```

Si esas rutas responden, la API esta viva. Si el navegador falla pero curl responde, revisar primero:

- `VITE_API_BASE_URL` en Vercel.
- Redeploy del frontend.
- CORS en Render.
- Pestaña Network del navegador para ver la URL exacta que React esta llamando.
