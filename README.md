# N8N API

這是一個用於支援 N8N 整合的 FastAPI 專案。

## 安裝

### 使用 Poetry（推薦）

1. 安裝 Poetry（如果尚未安裝）：
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. 安裝依賴：
```bash
poetry install
```

3. 啟動虛擬環境：
```bash
poetry shell
```

### 使用 pip（替代方案）

1. 創建虛擬環境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

2. 安裝依賴：
```bash
pip install -r requirements.txt
```

## 配置

1. 配置環境變數：
- 複製 `.env.example` 到 `.env`
- 修改 `.env` 中的配置

## 運行

```bash
# 使用 Poetry
poetry run uvicorn app.main:app --reload

# 或使用 pip
uvicorn app.main:app --reload
```

## API 文檔

啟動服務後，可以訪問以下地址查看 API 文檔：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 開發工具

### 程式碼格式化
```bash
# 使用 Poetry
poetry run black .
poetry run isort .

# 或使用 pip
black .
isort .
```

### 型別檢查
```bash
# 使用 Poetry
poetry run mypy .

# 或使用 pip
mypy .
```

### 測試
```bash
# 使用 Poetry
poetry run pytest

# 或使用 pip
pytest
```

## 專案結構

```
app/
├── api/
│   └── v1/
│       ├── endpoints/
│       │   └── finance.py
│       └── api.py
├── core/
│   └── config.py
└── main.py
```

## 部署到 Zeabur

1. 確保您的專案根目錄有 `pyproject.toml` 文件
2. 在 Zeabur 上創建新的 Python 專案
3. 連接您的 Git 倉庫
4. Zeabur 會自動識別 Poetry 配置並使用它來管理依賴

注意：確保在 Zeabur 的環境變數中設置所有必要的配置（如 N8N_API_URL, N8N_API_KEY 等） 