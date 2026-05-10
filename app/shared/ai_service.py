import re
import json
from app.core.config import settings
# Nueva forma de importar en LangChain >= 0.3
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

class AIService:
    def __init__(self):
        # Verificar que la API key existe
        if not settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY no configurada. "
                "Agrégala en tu archivo .env"
            )
        
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,  # ← Toma del .env automáticamente
            model=settings.openai_model,
            temperature=settings.openai_temperature
        )
    async def extract_invoice_items(self, text: str) -> list:
        """Extrae items de factura desde texto no estructurado"""
        prompt = f"""
        Extrae todos los items de esta factura médica.
        
        Factura:
        {text[:2000]}
        
        Responde SOLO con JSON en este formato:
        [{{"nombre": "descripcion del item", "cantidad": 1, "precio_unitario": 100.0, "tipo": "insumo"}}]
        
        Si no hay items claros, responde: []
        """
        
        try:
            response = await self.llm.apredict(prompt)
            # Limpiar markdown si existe
            clean = re.sub(r'```json\n?|```', '', response.strip())
            return json.loads(clean)
        except Exception as e:
            print(f"Error extrayendo items: {e}")
            return []
    
    async def detect_anomalies(self, items: list, case_info: dict) -> dict:
        """Detecta anomalías en los items facturados"""
        prompt = f"""
        Eres un auditor de seguros. Analiza estos items facturados contra el caso.
        
        Items facturados:
        {json.dumps(items, indent=2)}
        
        Información del siniestro:
        - Tipo: {case_info.get('tipo', 'no especificado')}
        - Diagnóstico: {case_info.get('diagnostico', 'no especificado')}
        - Insumos esperados: {case_info.get('insumos_esperados', [])}
        - Honorarios esperados: {case_info.get('honorarios_esperados', [])}
        
        Detecta:
        1. Items con precio sospechosamente alto
        2. Items que no corresponden al tipo de siniestro
        3. Posibles duplicados
        
        Responde SOLO con JSON:
        {{
            "anomalias": [
                {{"tipo": "precio_alto|item_inconsistente|duplicado", "descripcion": "detalle", "item": "nombre del item"}}
            ],
            "es_valido": true/false,
            "recomendacion": "texto breve"
        }}
        """
        
        try:
            response = await self.llm.apredict(prompt)
            clean = re.sub(r'```json\n?|```', '', response.strip())
            return json.loads(clean)
        except Exception as e:
            print(f"Error detectando anomalías: {e}")
            return {"anomalias": [], "es_valido": True, "recomendacion": "No se pudo analizar con IA"}