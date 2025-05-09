from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.v1.api import api_router
from app.core.config import settings
import os

app = FastAPI(
    title="N8N API",
    description="API for N8N integration with FFmpeg and Yahoo Finance support",
    version="1.0.0"
)

# CORS 設置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 掛載靜態文件目錄
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 包含 API 路由
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "message": "Welcome to N8N API",
        "version": "1.0.0",
        "features": [
            "N8N Workflow Integration",
            "FFmpeg Video Processing",
            "Yahoo Finance Data"
        ]
    }

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("app/static/favicon.ico")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 