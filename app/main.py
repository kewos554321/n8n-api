from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.v1.api import api_router
from app.core.config import settings
import os
from pydantic import BaseModel, HttpUrl
from playwright.async_api import async_playwright
import asyncio
from typing import Optional

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

class URLRequest(BaseModel):
    url: HttpUrl
    wait_time: Optional[int] = 5  # 等待時間（秒）

class ScrapeResponse(BaseModel):
    title: str
    content: str
    status: int

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_url(request: URLRequest):
    try:
        async with async_playwright() as p:
            # 啟動瀏覽器，添加額外的參數來模擬真實瀏覽器
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                    '--window-size=1920,1080',
                ]
            )
            
            # 創建新的上下文，設置用戶代理
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                java_script_enabled=True,
                ignore_https_errors=True,
                bypass_csp=True,
            )
            
            # 創建新頁面
            page = await context.new_page()
            
            # 設置額外的 headers
            await page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            })
            
            # 設置超時時間
            page.set_default_timeout(60000)  # 60 seconds
            
            try:
                # 訪問頁面
                response = await page.goto(
                    str(request.url),
                    wait_until='domcontentloaded',  # 改用 domcontentloaded 而不是 networkidle
                    timeout=60000  # 60 seconds
                )
                
                if not response:
                    raise HTTPException(status_code=400, detail="Failed to load page")
                
                # 等待指定時間
                await asyncio.sleep(request.wait_time)
                
                # 獲取頁面內容
                title = await page.title()
                content = await page.content()
                
                return ScrapeResponse(
                    title=title,
                    content=content,
                    status=response.status
                )
                
            except Exception as e:
                # 如果頁面加載失敗，嘗試獲取當前內容
                try:
                    title = await page.title()
                    content = await page.content()
                    return ScrapeResponse(
                        title=title,
                        content=content,
                        status=500
                    )
                except:
                    raise HTTPException(status_code=500, detail=str(e))
            finally:
                # 確保瀏覽器被關閉
                await browser.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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