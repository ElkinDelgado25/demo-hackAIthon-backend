import asyncio

from app.business_rules.models import BusinessRule
from app.cases.models import Case
from app.database.mongo import close_mongo_connection, init_mongo
from app.shared.enums import CaseStatus, RuleOperator, RuleStatus, RuleType, Severity


DEMO_CASES = [
    {
        "claim_number": "SIN-2026-004",
        "workshop": "Taller Norte",
        "vehicle": {"brand": "Kia", "model": "Sportage", "year": 2021},
        "plate": "PBT-4921",
        "reported_damages": ["parachoques delantero", "farola derecha"],
        "invoice_total": 1380,
        "tariff_total": 1120,
        "status": CaseStatus.NUEVO,
    },
    {
        "claim_number": "SIN-2026-018",
        "workshop": "Multiservicios Andinos",
        "vehicle": {"brand": "Hyundai", "model": "Tucson", "year": 2020},
        "plate": "GSK-7102",
        "reported_damages": ["puerta posterior", "guardafango izquierdo"],
        "invoice_total": 860,
        "tariff_total": 910,
        "status": CaseStatus.PENDIENTE_DOCUMENTOS,
    },
    {
        "claim_number": "SIN-2026-031",
        "workshop": "Diesel Sur",
        "vehicle": {"brand": "Chevrolet", "model": "D-Max", "year": 2019},
        "plate": "MBD-3390",
        "reported_damages": ["balde", "stop posterior"],
        "invoice_total": 2210,
        "tariff_total": 1650,
        "status": CaseStatus.NUEVO,
    },
    {
        "claim_number": "SIN-2026-047",
        "workshop": "Carroceria Express",
        "vehicle": {"brand": "Renault", "model": "Duster", "year": 2022},
        "plate": "RND-8451",
        "reported_damages": ["capot", "radiador"],
        "invoice_total": 1740,
        "tariff_total": 1700,
        "status": CaseStatus.LISTO_PARA_AUDITORIA,
    },
    {
        "claim_number": "SIN-2026-052",
        "workshop": "AutoCentro Pacifico",
        "vehicle": {"brand": "Nissan", "model": "Versa", "year": 2023},
        "plate": "NVS-6029",
        "reported_damages": ["parachoques trasero"],
        "invoice_total": 520,
        "tariff_total": 490,
        "status": CaseStatus.NUEVO,
    },
    {
        "claim_number": "SIN-2026-066",
        "workshop": "TecniAuto Valle",
        "vehicle": {"brand": "Suzuki", "model": "Vitara", "year": 2021},
        "plate": "SVT-1187",
        "reported_damages": ["retrovisor derecho", "puerta derecha"],
        "invoice_total": 980,
        "tariff_total": 1040,
        "status": CaseStatus.NUEVO,
    },
]

DEMO_RULES = [
    {
        "name": "Factura obligatoria",
        "description": "Todo caso debe contener factura.",
        "type": RuleType.DOCUMENTO_OBLIGATORIO,
        "target_field": "documents",
        "operator": RuleOperator.CONTIENE,
        "reference_value": "FACTURA",
        "severity": Severity.ALTA,
        "status": RuleStatus.ACTIVA,
        "alert_message": "Falta factura del taller.",
    },
    {
        "name": "Orden de reparacion obligatoria",
        "description": "Todo caso debe contener orden de reparacion para validar trabajos autorizados.",
        "type": RuleType.DOCUMENTO_OBLIGATORIO,
        "target_field": "documents",
        "operator": RuleOperator.CONTIENE,
        "reference_value": "ORDEN_REPARACION",
        "severity": Severity.ALTA,
        "status": RuleStatus.ACTIVA,
        "alert_message": "Falta orden de reparacion autorizada.",
    },
    {
        "name": "Detalle de mano de obra obligatorio",
        "description": "Todo caso debe incluir detalle de mano de obra para revisar horas y actividades.",
        "type": RuleType.DOCUMENTO_OBLIGATORIO,
        "target_field": "documents",
        "operator": RuleOperator.CONTIENE,
        "reference_value": "DETALLE_MANO_OBRA",
        "severity": Severity.MEDIA,
        "status": RuleStatus.ACTIVA,
        "alert_message": "Falta detalle de mano de obra.",
    },
    {
        "name": "Fotos de dano obligatorias",
        "description": "Todo caso debe incluir fotografias del dano reportado.",
        "type": RuleType.DOCUMENTO_OBLIGATORIO,
        "target_field": "documents",
        "operator": RuleOperator.CONTIENE,
        "reference_value": "FOTOS_DANIO",
        "severity": Severity.MEDIA,
        "status": RuleStatus.ACTIVA,
        "alert_message": "Faltan fotografias del dano.",
    },
    {
        "name": "Tarifario para diferencias financieras",
        "description": "Todo caso con montos debe contener tarifario.",
        "type": RuleType.DOCUMENTO_OBLIGATORIO,
        "target_field": "documents",
        "operator": RuleOperator.CONTIENE,
        "reference_value": "TARIFARIO",
        "severity": Severity.MEDIA,
        "status": RuleStatus.ACTIVA,
        "alert_message": "Falta tarifario para contrastar valores.",
    },
    {
        "name": "Poliza para cobertura",
        "description": "La poliza permite validar cobertura, exclusiones y deducibles.",
        "type": RuleType.DOCUMENTO_OBLIGATORIO,
        "target_field": "documents",
        "operator": RuleOperator.CONTIENE,
        "reference_value": "POLIZA",
        "severity": Severity.ALTA,
        "status": RuleStatus.ACTIVA,
        "alert_message": "Falta poliza para validar cobertura.",
    },
    {
        "name": "Variacion financiera mayor al 25 por ciento",
        "description": "Marca diferencias altas entre factura y tarifario para revision humana.",
        "type": RuleType.PORCENTAJE_VARIACION,
        "target_field": "invoiceTotal",
        "operator": RuleOperator.MAYOR_QUE,
        "reference_value": "25",
        "severity": Severity.CRITICA,
        "status": RuleStatus.ACTIVA,
        "alert_message": "La factura presenta una variacion critica frente al tarifario.",
    },
    {
        "name": "Item duplicado en factura",
        "description": "Detecta posibles repuestos o actividades cobradas mas de una vez.",
        "type": RuleType.ITEM_DUPLICADO,
        "target_field": "invoiceItems",
        "operator": RuleOperator.CONTIENE,
        "reference_value": "duplicado",
        "severity": Severity.ALTA,
        "status": RuleStatus.ACTIVA,
        "alert_message": "Posible cobro duplicado detectado.",
    },
    {
        "name": "Item no relacionado al dano",
        "description": "Marca items que no correspondan a los danos reportados.",
        "type": RuleType.ITEM_NO_RELACIONADO,
        "target_field": "reportedDamages",
        "operator": RuleOperator.NO_CONTIENE,
        "reference_value": "dano_reportado",
        "severity": Severity.ALTA,
        "status": RuleStatus.ACTIVA,
        "alert_message": "Existe un item que no parece relacionado con el dano reportado.",
    },
    {
        "name": "Mano de obra excesiva",
        "description": "Marca cantidades de mano de obra que excedan parametros esperados.",
        "type": RuleType.CANTIDAD_MAXIMA,
        "target_field": "laborHours",
        "operator": RuleOperator.MAYOR_QUE,
        "reference_value": "12",
        "severity": Severity.MEDIA,
        "status": RuleStatus.ACTIVA,
        "alert_message": "La mano de obra reportada parece excesiva para el dano declarado.",
    },
]


async def seed() -> None:
    await init_mongo()

    for item in DEMO_CASES:
        existing = await Case.find_one(Case.claim_number == item["claim_number"])
        if not existing:
            await Case(**item).insert()

    for item in DEMO_RULES:
        existing = await BusinessRule.find_one(BusinessRule.name == item["name"])
        if not existing:
            await BusinessRule(**item).insert()

    close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(seed())
