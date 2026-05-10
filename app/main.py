from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routes import router as auth_router
from app.audits.routes import router as audits_router
from app.business_rules.routes import router as business_rules_router
from app.cases.routes import router as cases_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.dashboard.routes import router as dashboard_router
from app.database.mongo import close_mongo_connection, init_mongo


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="API para auditoria de facturacion de siniestros.",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    @app.on_event("startup")
    async def on_startup() -> None:
        await init_mongo()

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        close_mongo_connection()

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(cases_router, prefix=settings.api_prefix)
    app.include_router(audits_router, prefix=settings.api_prefix)
    app.include_router(business_rules_router, prefix=settings.api_prefix)
    app.include_router(dashboard_router, prefix=settings.api_prefix)
    return app


app = create_app()
