from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.audits.models import Audit
from app.business_rules.models import BusinessRule
from app.cases.models import Case, CaseDocument
from app.core.config import settings
from app.database.init_db import ensure_default_admin
from app.users.models import User

client: AsyncIOMotorClient | None = None


async def init_mongo() -> None:
    global client
    client = AsyncIOMotorClient(settings.mongodb_uri)
    database = client[settings.mongodb_db]
    await init_beanie(database=database, document_models=[User, Case, CaseDocument, Audit, BusinessRule])
    await ensure_default_admin()


def close_mongo_connection() -> None:
    if client:
        client.close()
