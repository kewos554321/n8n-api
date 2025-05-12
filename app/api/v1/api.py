from fastapi import APIRouter
from app.api.v1.endpoints import finance, cron

api_router = APIRouter()
api_router.include_router(finance.router, prefix="/finance", tags=["finance"])
api_router.include_router(cron.router, prefix="/cron", tags=["cron"]) 