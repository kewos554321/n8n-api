from fastapi import APIRouter
from app.api.v1.endpoints import finance

api_router = APIRouter()
api_router.include_router(finance.router, prefix="/finance", tags=["finance"]) 