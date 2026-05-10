from app.core.config import settings
from langchain.chat_models import ChatOpenAI

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