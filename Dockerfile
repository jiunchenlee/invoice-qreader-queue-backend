FROM python:3.9-slim

# 安裝系統依賴 (zbar, OpenGL, glib)
RUN apt-get update && apt-get install -y \
    libzbar0 \
    libglx0 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 複製依賴清單
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY . .

# 設定環境變數
ENV PYTHONUNBUFFERED=1

# 預設啟動指令 (API) - 使用 sh -c 確保 $PORT 變數能被正確解析
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]