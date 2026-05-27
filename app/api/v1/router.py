from fastapi import APIRouter

from app.api.v1.routes import auth, documents, health, orders

router = APIRouter(prefix="/api/v1")

router.include_router(health.router, tags=["health"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(orders.router, prefix="/orders", tags=["orders"])
router.include_router(documents.router, prefix="/documents", tags=["documents"])
