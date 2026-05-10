# test_openai.py
#from app.core.config import settings

#print(f"API Key existe: {settings.openai_api_key is not None}")
#print(f"Modelo: {settings.openai_model}")
#print(f"Temperature: {settings.openai_temperature}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# Leer origins desde .env
origins = os.getenv("BACKEND_CORS_ORIGINS", "").split(",")

print("CORS ORIGINS:")
print(origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Backend funcionando correctamente"
    }

@app.get("/test-cors")
async def test_cors():
    return {
        "status": "success",
        "message": "CORS funcionando"
    }