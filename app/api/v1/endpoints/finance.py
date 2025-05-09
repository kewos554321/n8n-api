import yfinance as yf
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.core.config import settings

router = APIRouter()

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
        
        return {
            "total": len(stock_list),
            "market": market,
            "stocks": stock_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stocks: {str(e)}")

@router.get("/stock/{symbol}")
async def get_stock_info(symbol: str):
    """
    獲取特定股票的詳細信息
    """
    try:
        # 處理台股代碼
        if not symbol.endswith('.TW') and symbol.isdigit():
            symbol = f"{symbol}.TW"
            
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # 獲取最近3天的股價數據
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)
        hist = stock.history(start=start_date, end=end_date)
        
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")
        
        latest_price = hist['Close'].iloc[-1]
        
        # 根據市場調整返回的貨幣單位
        currency = "TWD" if symbol.endswith('.TW') else info.get('currency', 'USD')
        
        return {
            "symbol": symbol,
            "name": info.get('longName', ''),
            "current_price": latest_price,
            "currency": currency,
            "market_cap": info.get('marketCap', 0),
            "sector": info.get('sector', ''),
            "industry": info.get('industry', ''),
            "exchange": info.get('exchange', ''),
            "previous_close": info.get('previousClose', 0),
            "open": info.get('open', 0),
            "day_high": info.get('dayHigh', 0),
            "day_low": info.get('dayLow', 0),
            "volume": info.get('volume', 0),
            "fifty_two_week_high": info.get('fiftyTwoWeekHigh', 0),
            "fifty_two_week_low": info.get('fiftyTwoWeekLow', 0),
            "dividend_yield": info.get('dividendYield', 0),
            "pe_ratio": info.get('trailingPE', 0),
            "eps": info.get('trailingEps', 0),
            "beta": info.get('beta', 0),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock info: {str(e)}")

@router.get("/stock/{symbol}/history")
async def get_stock_history(
    symbol: str,
    period: str = "1mo",
    interval: str = "1d"
):
    """
    獲取股票的歷史數據
    period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    """
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period, interval=interval)
        
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No historical data found for symbol {symbol}")
        
        # 將 DataFrame 轉換為字典列表
        history_data = []
        for index, row in hist.iterrows():
            history_data.append({
                "date": index.strftime("%Y-%m-%d %H:%M:%S"),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close']),
                "volume": int(row['Volume'])
            })
        
        return {
            "symbol": symbol,
            "period": period,
            "interval": interval,
            "data": history_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock history: {str(e)}")

@router.get("/stock/{symbol}/recommendations")
async def get_stock_recommendations(symbol: str):
    """
    獲取股票的推薦評級
    """
    try:
        stock = yf.Ticker(symbol)
        recommendations = stock.recommendations
        
        if recommendations is None or recommendations.empty:
            raise HTTPException(status_code=404, detail=f"No recommendations found for symbol {symbol}")
        
        # 將 DataFrame 轉換為字典列表
        recommendations_data = []
        for index, row in recommendations.iterrows():
            recommendations_data.append({
                "date": index.strftime("%Y-%m-%d"),
                "firm": row.get('Firm', ''),
                "to_grade": row.get('To Grade', ''),
                "from_grade": row.get('From Grade', ''),
                "action": row.get('Action', '')
            })
        
        return {
            "symbol": symbol,
            "recommendations": recommendations_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock recommendations: {str(e)}")

@router.get("/stock/{symbol}/news")
async def get_stock_news(symbol: str):
    """
    獲取股票的最新新聞
    """
    try:
        # 處理台股代碼
        if not symbol.endswith('.TW') and symbol.isdigit():
            symbol = f"{symbol}.TW"
            
        stock = yf.Ticker(symbol)
        news = stock.news
        
        if not news:
            raise HTTPException(status_code=404, detail=f"No news found for symbol {symbol}")
        
        # 格式化新聞數據
        formatted_news = []
        for item in news:
            content = item.get('content', {})
            formatted_news.append({
                "title": content.get('title', ''),
                "summary": content.get('summary', ''),
                "publisher": content.get('provider', {}).get('displayName', ''),
                "published_at": content.get('pubDate', ''),
                "url": content.get('canonicalUrl', {}).get('url', ''),
                "thumbnail": content.get('thumbnail', {}).get('resolutions', [{}])[0].get('url', '') if content.get('thumbnail') else None
            })
        
        return {
            "symbol": symbol,
            "total_news": len(formatted_news),
            "news": formatted_news
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock news: {str(e)}")

