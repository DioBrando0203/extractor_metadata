from fastapi import APIRouter

from app.api.routes.geodata import router as geodata_router
from app.api.routes.health import router as health_router
from app.api.routes.messages import router as messages_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(geodata_router, prefix="/geodata", tags=["geodata"])
api_router.include_router(messages_router, prefix="/messages", tags=["messages"])
