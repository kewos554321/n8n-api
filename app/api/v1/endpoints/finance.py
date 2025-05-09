import finnhub
from fastapi import APIRouter, HTTPException, Query, WebSocket
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.logging_config import setup_logger
import json
import threading
import time
import asyncio

# 設置日誌記錄器
logger = setup_logger(__name__, "finance_api.log")

router = APIRouter()

# 初始化 Finnhub 客戶端
finnhub_client = finnhub.Client(api_key="d0esb69r01qlbf85mkq0d0esb69r01qlbf85mkqg")

# 預定義的股票列表
POPULAR_US_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META",  # 科技股
    "TSLA", "NVDA", "AMD", "INTC", "QCOM",    # 半導體
    "JPM", "BAC", "V", "MA", "GS",            # 金融股
    "JNJ", "PFE", "MRK", "ABBV", "LLY",       # 醫療股
    "WMT", "COST", "TGT", "HD", "LOW",        # 零售股
    "XOM", "CVX", "COP", "SLB", "EOG",        # 能源股
    "DIS", "NFLX", "CMCSA", "T", "VZ"         # 媒體通訊
]

POPULAR_TW_STOCKS = [
    "2330.TW", "2317.TW", "2412.TW", "2882.TW", "1303.TW",  # 台積電、鴻海、中華電、國泰金、南亞
    "2454.TW", "2308.TW", "2303.TW", "2379.TW", "3034.TW",  # 聯發科、台達電、聯電、瑞昱、聯詠
    "2881.TW", "2884.TW", "2886.TW", "2891.TW", "2885.TW",  # 富邦金、玉山金、兆豐金、中信金、元大金
    "1301.TW", "1326.TW", "1402.TW", "2105.TW", "2207.TW",  # 台塑、台化、遠東新、正新、和泰車
    "2912.TW", "1216.TW", "1101.TW", "2002.TW", "2301.TW"   # 統一超、統一、台泥、中鋼、光寶科
]

@router.get("/stocks")
async def list_stocks(
    market: str = Query("all", description="Market to fetch stocks from (all, us, tw)"),
    limit: int = Query(100, description="Maximum number of stocks to return")
):
    """
    獲取股票列表
    - market: 市場選擇 (all, us, tw)
    - limit: 返回的最大股票數量
    """
    try:
        logger.info(f"Fetching stocks for market: {market} with limit: {limit}")
        stocks = set()
        
        if market in ["all", "us"]:
            stocks.update(POPULAR_US_STOCKS)
        
        if market in ["all", "tw"]:
            stocks.update(POPULAR_TW_STOCKS)
        
        # 轉換為列表並排序
        stock_list = sorted(list(stocks))
        
        # 限制返回數量
        if limit > 0:
            stock_list = stock_list[:limit]
        
        logger.info(f"Successfully fetched {len(stock_list)} stocks")
        return {
            "total": len(stock_list),
            "market": market,
            "stocks": stock_list
        }
    except Exception as e:
        logger.error(f"Failed to fetch stocks: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch stocks: {str(e)}")

@router.get("/stock/{symbol}")
async def get_stock_info(symbol: str):
    """
    獲取特定股票的詳細信息
    """
    try:
        logger.info(f"Fetching stock info for symbol: {symbol}")
        
        # 處理台股代碼
        if not symbol.endswith('.TW') and symbol.isdigit():
            symbol = f"{symbol}.TW"
        
        # 獲取股票基本信息
        quote = finnhub_client.quote(symbol)
        company_profile = finnhub_client.company_profile2(symbol=symbol)
        
        if not quote or not company_profile:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")
        
        # 獲取股票新聞
        news = finnhub_client.company_news(symbol, _from=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                                         to=datetime.now().strftime('%Y-%m-%d'))
        
        return {
            "symbol": symbol,
            "name": company_profile.get('name', ''),
            "current_price": quote.get('c', 0),
            "currency": "TWD" if symbol.endswith('.TW') else "USD",
            "market_cap": company_profile.get('marketCapitalization', 0),
            "sector": company_profile.get('finnhubIndustry', ''),
            "industry": company_profile.get('finnhubIndustry', ''),
            "exchange": company_profile.get('exchange', ''),
            "previous_close": quote.get('pc', 0),
            "open": quote.get('o', 0),
            "day_high": quote.get('h', 0),
            "day_low": quote.get('l', 0),
            "volume": quote.get('t', 0),
            "fifty_two_week_high": quote.get('h52', 0),
            "fifty_two_week_low": quote.get('l52', 0),
            "pe_ratio": company_profile.get('pe', 0),
            "eps": company_profile.get('eps', 0),
            "beta": company_profile.get('beta', 0),
            "latest_news": news[:5] if news else [],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch stock info for {symbol}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock info: {str(e)}")

@router.get("/stock/{symbol}/history")
async def get_stock_history(
    symbol: str,
    from_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: str = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    獲取股票的歷史數據
    """
    try:
        # 處理台股代碼
        if not symbol.endswith('.TW') and symbol.isdigit():
            symbol = f"{symbol}.TW"
        
        # 如果沒有指定日期，使用過去30天
        if not from_date:
            from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not to_date:
            to_date = datetime.now().strftime('%Y-%m-%d')
        
        # 獲取歷史數據
        hist = finnhub_client.stock_candles(symbol, 'D', int(datetime.strptime(from_date, '%Y-%m-%d').timestamp()),
                                          int(datetime.strptime(to_date, '%Y-%m-%d').timestamp()))
        
        if hist['s'] != 'ok':
            raise HTTPException(status_code=404, detail=f"No historical data found for symbol {symbol}")
        
        # 格式化數據
        history_data = []
        for i in range(len(hist['t'])):
            history_data.append({
                "date": datetime.fromtimestamp(hist['t'][i]).strftime("%Y-%m-%d %H:%M:%S"),
                "open": hist['o'][i],
                "high": hist['h'][i],
                "low": hist['l'][i],
                "close": hist['c'][i],
                "volume": hist['v'][i]
            })
        
        return {
            "symbol": symbol,
            "from_date": from_date,
            "to_date": to_date,
            "data": history_data
        }
    except Exception as e:
        logger.error(f"Failed to fetch stock history for {symbol}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock history: {str(e)}")

@router.get("/stock/{symbol}/news")
async def get_stock_news(symbol: str):
    """
    獲取股票的最新新聞
    """
    try:
        logger.info(f"Fetching news for symbol: {symbol}")
        
        # 處理台股代碼
        is_tw_stock = False
        if not symbol.endswith('.TW') and symbol.isdigit():
            symbol = f"{symbol}.TW"
            is_tw_stock = True
        
        # 獲取過去7天的新聞
        try:
            if is_tw_stock:
                # 對於台股，直接使用一般新聞並過濾
                news = finnhub_client.general_news('general', min_id=0)
                # 過濾相關新聞，包括股票代碼和公司名稱
                filtered_news = []
                for item in news:
                    headline = item.get('headline', '').lower()
                    summary = item.get('summary', '').lower()
                    # 移除 .TW 後綴進行匹配
                    symbol_base = symbol.replace('.TW', '')
                    if (symbol_base in headline or symbol_base in summary or
                        symbol in headline or symbol in summary):
                        filtered_news.append(item)
                news = filtered_news
            else:
                # 對於美股，使用公司新聞
                news = finnhub_client.company_news(
                    symbol,
                    _from=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                    to=datetime.now().strftime('%Y-%m-%d')
                )
        except Exception as e:
            logger.error(f"Error fetching news: {str(e)}")
            news = []
        
        if not news:
            logger.warning(f"No news found for symbol {symbol}")
            return {
                "symbol": symbol,
                "total_news": 0,
                "news": [],
                "message": "No news found for this symbol"
            }
        
        # 格式化新聞數據
        formatted_news = []
        for item in news:
            try:
                formatted_news.append({
                    "title": item.get('headline', ''),
                    "summary": item.get('summary', ''),
                    "publisher": item.get('source', ''),
                    "published_at": datetime.fromtimestamp(item.get('datetime', 0)).strftime("%Y-%m-%d %H:%M:%S"),
                    "url": item.get('url', ''),
                    "category": item.get('category', ''),
                    "image": item.get('image', '')
                })
            except Exception as e:
                logger.error(f"Error formatting news item: {str(e)}")
                continue
        
        logger.info(f"Successfully fetched {len(formatted_news)} news items for {symbol}")
        return {
            "symbol": symbol,
            "total_news": len(formatted_news),
            "news": formatted_news
        }
    except Exception as e:
        logger.error(f"Failed to fetch stock news for {symbol}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock news: {str(e)}")

@router.get("/test/{symbol}")
async def test_stock_fetch(symbol: str):
    """
    測試股票資料獲取
    """
    try:
        logger.info(f"Testing stock fetch for symbol: {symbol}")
        
        # 處理台股代碼
        if not symbol.endswith('.TW') and symbol.isdigit():
            symbol = f"{symbol}.TW"
            
        stock = finnhub_client.quote(symbol)
        info = stock
        
        return {
            "symbol": symbol,
            "status": "success",
            "data": info
        }
        
    except Exception as e:
        logger.error(f"Test failed for {symbol}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

@router.websocket("/ws/test")
async def websocket_test(websocket: WebSocket):
    """
    測試 WebSocket 連接
    """
    await websocket.accept()
    
    def on_message(ws, message):
        try:
            # 將消息發送到客戶端
            asyncio.run(websocket.send_text(message))
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
    
    def on_error(ws, error):
        logger.error(f"WebSocket error: {str(error)}")
        try:
            asyncio.run(websocket.send_text(f"Error: {str(error)}"))
        except Exception as e:
            logger.error(f"Error sending error message: {str(e)}")
    
    def on_close(ws, close_status_code, close_msg):
        logger.info("WebSocket connection closed")
        try:
            asyncio.run(websocket.send_text("Connection closed"))
        except Exception as e:
            logger.error(f"Error sending close message: {str(e)}")
    
    def on_open(ws):
        logger.info("WebSocket connection opened")
        # 訂閱股票新聞
        symbols = ["AAPL", "AMZN", "MSFT", "BYND"]
        for symbol in symbols:
            ws.send(json.dumps({
                "type": "subscribe-news",
                "symbol": symbol
            }))
    
    try:
        # 創建 WebSocket 連接
        ws = websocket.WebSocketApp(
            "wss://ws.finnhub.io?token=d0esb69r01qlbf85mkq0d0esb69r01qlbf85mkqg",
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        ws.on_open = on_open
        
        # 在新線程中運行 WebSocket
        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        # 保持連接開啟
        while True:
            try:
                # 等待客戶端消息
                data = await websocket.receive_text()
                logger.info(f"Received from client: {data}")
            except Exception as e:
                logger.error(f"Error receiving message: {str(e)}")
                break
            
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()
    finally:
        if 'ws' in locals():
            ws.close()

@router.get("/finnhub/news")
async def test_finnhub_news():
    """
    測試 Finnhub 新聞 API
    """
    try:
        logger.info("Testing Finnhub news API")
        
        # 獲取一般新聞
        news = finnhub_client.general_news('general', min_id=0)
        
        logger.info(f"Successfully fetched {len(news)} news items")
        return {
            "status": "success",
            "total_news": len(news),
            "news": news
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch Finnhub news: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch news: {str(e)}")

