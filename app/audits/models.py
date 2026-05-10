# app/audits/models.py
from datetime import datetime
from typing import List, Optional
from beanie import Document
from pydantic import BaseModel
from enum import Enum


class AuditStatus(str, Enum):
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    OBSERVACIONES = "observaciones"
    PENDIENTE = "pendiente"


class Discrepancia(BaseModel):
    tipo: str  # precio_excedido, duplicado, incoherencia_siniestro, item_no_tarifado
    descripcion: str
    item: Optional[str] = None
    valor_esperado: Optional[float] = None
    valor_encontrado: Optional[float] = None


class Audit(Document):
    case_id: str
    document_name: str
    status: AuditStatus
    total_discrepancias: int
    discrepancias: List[Discrepancia]
    resumen_ejecutivo: str
    detalles_auditoria: dict
    created_at: datetime
    
    class Settings:
        name = "audits"