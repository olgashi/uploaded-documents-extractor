from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import router as api_v1_router
from app.core.config import settings
from app.core.limiter import limiter
from app.core.logging import configure_logging
from app.middleware.activity_log import ActivityLogMiddleware
from app.services.auth_service import seed_admin

configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", environment=settings.ENVIRONMENT, model=settings.OPENAI_MODEL)
    await seed_admin()
    yield
    logger.info("shutdown")


app = FastAPI(
    title="Document Extractor API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(ActivityLogMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)
