# test_openai.py
from app.core.config import settings

print(f"API Key existe: {settings.openai_api_key is not None}")
print(f"Modelo: {settings.openai_model}")
print(f"Temperature: {settings.openai_temperature}")