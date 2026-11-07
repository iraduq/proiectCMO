from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse
from app.api.routers.absences import router as absences_router
from app.api.routers.auth import router as auth_router
from app.api.routers.classes import router as classes_router
from app.api.routers.dashboard import router as dashboard_router
from app.api.routers.grades import router as grades_router
from app.api.routers.health import router as health_router
from app.api.routers.notifications import router as notifications_router
from app.api.routers.parent import router as parent_router
from app.api.routers.remarks import router as remarks_router
from app.config import settings
from app.db.database import AsyncSessionLocal, Base, engine
from app.db.seed import seed_all
from app.middleware.exception_handler import register_exception_handlers
from app.middleware.security import security_middleware

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await seed_all(session)
    yield
    await engine.dispose()

app = FastAPI(
    title="EduGrade API - Catalog Digital Multi-Rol",
    description=(
        "Backend cloud securizat pentru aplicatia Android EduGrade. "
        "Suporta roluri multiple: Elevi, Parinti, Profesori, Administratori. "
        "Permite vizualizarea notelor, calculul automat al mediilor, consemnarea si motivarea absentelor, "
        "aprecieri/mentiuni si notificari in timp real."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

def custom_openapi() -> dict:
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="EduGrade API - Catalog Digital Multi-Rol",
        version="1.0.0",
        description="Catalog digital securizat in cloud pentru elevi, parinti si profesori.",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/api/auth/token",
                    "scopes": {},
                }
            },
        }
    }

    for path, methods in openapi_schema.get("paths", {}).items():
        for method, operation in methods.items():
            responses = operation.setdefault("responses", {})
            responses.setdefault("400", {"description": "Cerere invalida / Date incorecte"})
            responses.setdefault("401", {"description": "Neautentificat / Token lipsa sau expirat"})
            responses.setdefault("403", {"description": "Acces interzis / Drepturi insuficiente"})
            responses.setdefault("404", {"description": "Resursa nu a fost gasita"})

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

register_exception_handlers(app)
app.middleware("http")(security_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

app.include_router(health_router)
app.include_router(auth_router, prefix="/api")
app.include_router(grades_router, prefix="/api")
app.include_router(absences_router, prefix="/api")
app.include_router(remarks_router, prefix="/api")
app.include_router(classes_router, prefix="/api")
app.include_router(parent_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
