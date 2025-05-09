FROM python:3.9-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# 複製 Poetry 配置文件
COPY pyproject.toml poetry.lock* ./

# 安裝依賴
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# 複製應用代碼
COPY . .

# 暴露端口
EXPOSE 8000

# 設置環境變量
ENV PYTHONPATH=/app
ENV PORT=8000

# 啟動命令 (添加性能優化參數)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--limit-concurrency", "1000", "--timeout-keep-alive", "30"] 