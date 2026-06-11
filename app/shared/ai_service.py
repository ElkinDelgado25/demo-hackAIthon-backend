import json
import re
from typing import Any

from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings

SECUREMAX_SYSTEM_MESSAGE = """Eres SecureMAX, un agente auditor especializado exclusivamente en siniestros vehiculares y auditoria documental para aseguradoras.

Tu funcion es analizar:

* casos de siniestros
* polizas
* cobertura
* tarifarios
* facturas
* ordenes de reparacion
* detalle de mano de obra
* repuestos
* insumos
* fotografias del dano
* sustento documental
* discrepancias financieras y operativas

Debes detectar:

* cobros duplicados
* precios superiores al tarifario
* mano de obra excesiva
* documentos faltantes
* items fuera de cobertura
* items no relacionados con los danos reportados
* inconsistencias entre factura, poliza y siniestralidad
* casos que requieran revision humana

NO debes:

* inventar informacion
* responder temas fuera del dominio asegurador
* realizar busquedas externas
* responder programacion general
* hablar de politica o entretenimiento

Si falta informacion responde:
'Dato no disponible'
e indica exactamente que dato hace falta.

La salida debe ser:

* objetiva
* tecnica
* estructurada
* corta y trazable

Siempre devolver:

* status sugerido
* findings
* severidad
* recommendation
* discrepancies
* documentos faltantes

Criterio de decision:

* No debes denegar automaticamente por documentos faltantes o diferencias financieras pequenas.
* Si faltan documentos, normalmente el status sugerido debe ser OBSERVADO o REVISION_HUMANA.
* Solo sugiere DENEGADO cuando exista una discrepancia critica de cobertura, fraude, duplicidad grave o diferencia financiera material.
* Usa las reglas de negocio entregadas por el sistema como fuente principal de validacion."""


class AIService:
    def __init__(self) -> None:
        if not settings.openai_api_key:
            self.llm = None
            return

        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=settings.openai_temperature,
        )

    async def extract_invoice_items(self, text: str) -> list:
        prompt = f"""
        Extrae todos los items de esta factura de reparacion vehicular.

        Factura:
        {text[:4000]}

        Responde SOLO con JSON:
        [{{"nombre": "descripcion", "cantidad": 1, "precio_unitario": 100.0, "tipo": "repuesto|mano_obra|insumo"}}]

        Si no hay items claros, responde: []
        """

        if not self.llm:
            return []

        try:
            response = await self.llm.apredict_messages([
                SystemMessage(content=SECUREMAX_SYSTEM_MESSAGE),
                HumanMessage(content=prompt),
            ])
            return json.loads(_clean_json(response.content))
        except Exception:
            return []

    async def audit_case(self, context: dict[str, Any]) -> dict[str, Any]:
        if not self.llm:
            return {}

        prompt = f"""
        Analiza este caso y devuelve SOLO JSON valido.

        Contexto:
        {json.dumps(context, ensure_ascii=False, indent=2)[:12000]}

        Formato:
        {{
          "status": "APROBADO|OBSERVADO|DENEGADO|REVISION_HUMANA",
          "riskScore": 0,
          "summary": "texto breve",
          "findings": [],
          "discrepancies": [],
          "topReasons": [],
          "recommendation": "texto breve"
        }}

        Reglas de salida:
        - No devuelvas findings ni discrepancies vacios.
        - No uses "Dato no disponible" como type, message, reason o title.
        - Si no puedes sustentar una discrepancia con los documentos, no la incluyas.
        - Cada discrepancy debe tener type, message y severity.
        """

        try:
            response = await self.llm.apredict_messages([
                SystemMessage(content=SECUREMAX_SYSTEM_MESSAGE),
                HumanMessage(content=prompt),
            ])
            return json.loads(_clean_json(response.content))
        except Exception:
            return {}

    async def detect_anomalies(self, items: list, case_info: dict) -> dict:
        result = await self.audit_case({"items": items, "caseInfo": case_info})
        if not result:
            return {"anomalias": [], "es_valido": True, "recomendacion": "Dato no disponible"}
        return {
            "anomalias": result.get("discrepancies", []),
            "es_valido": result.get("status") == "APROBADO",
            "recomendacion": result.get("recommendation", "Dato no disponible"),
        }


def _clean_json(value: str) -> str:
    return re.sub(r"```json\n?|```", "", value.strip())
