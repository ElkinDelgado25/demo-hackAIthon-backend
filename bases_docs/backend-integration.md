# Integracion del auditor con el backend

Esta guia deja la automatizacion fuera del frontend. React solo envia documentos, solicita auditorias y muestra resultados reales entregados por FastAPI.

## Objetivo

El backend debe encargarse de:

- Recibir y almacenar documentos del caso.
- Ejecutar el motor de auditoria.
- Consultar reglas de negocio.
- Persistir resultados e historial.
- Exponer estadisticas del dashboard.
- Manejar credenciales, webhooks internos o conexiones con servicios externos.

## Variables del frontend

El frontend solo necesita:

```bash
VITE_API_BASE_URL=http://localhost:8000/api
```

No agregues credenciales ni URLs privadas en React. Todo secreto debe vivir en el backend.

## Endpoints que consume React

Casos:

- `GET /cases`
- `GET /cases/{caseId}`

Documentos:

- `GET /cases/{caseId}/documents`
- `POST /cases/{caseId}/documents`

Auditoria:

- `POST /audit/{caseId}`
- `GET /audit/{caseId}/latest`
- `GET /audit/{caseId}/history`

Reglas:

- `GET /business-rules`
- `POST /business-rules`
- `PUT /business-rules/{ruleId}`
- `PATCH /business-rules/{ruleId}/toggle`
- `DELETE /business-rules/{ruleId}`

Estadisticas:

- `GET /statistics/dashboard`
- `GET /statistics/denial-reasons`

## Flujo esperado

1. El taller abre `/dashboard/cases`.
2. React consulta `GET /cases`.
3. El usuario selecciona un caso.
4. React consulta `GET /cases/{caseId}`.
5. El usuario sube documentos en `/dashboard/cases/{caseId}/upload`.
6. React envia `multipart/form-data` a `POST /cases/{caseId}/documents`.
7. React llama `POST /audit/{caseId}`.
8. FastAPI ejecuta el motor de auditoria y guarda el resultado.
9. React navega a `/dashboard/cases/{caseId}/result`.
10. React consulta `GET /audit/{caseId}/latest` si no recibe resultado directo.

## Payload recomendado para auditoria

```json
{
  "caseId": "SIN-2026-001",
  "vehicle": {
    "plate": "ABC-1234",
    "model": "Toyota Corolla 2020"
  },
  "reportedDamages": [],
  "documents": [
    {
      "name": "factura.pdf",
      "type": "FACTURA",
      "size": 123456,
      "mimeType": "application/pdf"
    }
  ],
  "requestedBy": "Taller",
  "source": "frontend-dashboard"
}
```

## Respuesta recomendada para resultado

```json
{
  "auditId": "AUD-001",
  "caseId": "SIN-2026-001",
  "status": "OBSERVADO",
  "confidence": 0.91,
  "summary": "Se detectaron diferencias entre la factura y el tarifario.",
  "discrepancies": [],
  "recommendation": "Solicitar correccion de factura o soporte adicional.",
  "createdAt": "2026-05-10T12:00:00Z"
}
```

## Respuesta de estadisticas

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

## Manejo de errores

FastAPI debe responder errores con una estructura simple:

```json
{
  "detail": "No se pudo ejecutar la auditoria para este caso."
}
```

El frontend mostrara un mensaje controlado si recibe un error HTTP o si la API no responde.

## Checklist backend

- Crear modelos de caso, documento, regla, resultado e historial.
- Guardar archivos recibidos desde `POST /cases/{caseId}/documents`.
- Validar documentos obligatorios antes de auditar.
- Ejecutar reglas de negocio desde el backend.
- Guardar cada auditoria en historial.
- Exponer el ultimo resultado por caso.
- Exponer estadisticas reales del dashboard.
- Mantener credenciales y conexiones privadas solo en variables del backend.
