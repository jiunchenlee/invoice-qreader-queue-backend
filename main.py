import os
import uuid
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from redis import Redis

app = FastAPI(title="Invoice Queue API")

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://default:TjVSiTlscOkTrhUMXqyFmcHpPaFhDRsW@redis.railway.internal:6379")
redis_conn = Redis.from_url(REDIS_URL)

class EnqueueRequest(BaseModel):
    image_urls: list[str]

@app.get("/")
async def root():
    return {"service": "invoice-queue-backend", "status": "running"}

@app.post("/api/invoice/enqueue")
async def enqueue_task(req: EnqueueRequest):
    """
    接收圖片 URL 列表，建立任務並丟入 Redis 佇列
    """
    if not req.image_urls:
        raise HTTPException(status_code=400, detail="No image URLs provided")

    task_id = str(uuid.uuid4())
    
    # 建立初始狀態
    initial_status = {
        "status": "queued",
        "current": 0,
        "total": len(req.image_urls),
        "progress": 0,
        "message": "任務已在排隊中"
    }
    
    # 將狀態存入 Redis (保留 1 小時)
    redis_conn.setex(f"task_status:{task_id}", 3600, json.dumps(initial_status))
    
    # 將任務丟入佇列
    task_payload = {
        "task_id": task_id,
        "image_urls": req.image_urls
    }
    redis_conn.rpush("invoice_tasks", json.dumps(task_payload))
    
    return {"success": True, "task_id": task_id}

@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """
    查詢任務進度或結果
    """
    status_raw = redis_conn.get(f"task_status:{task_id}")
    if not status_raw:
        raise HTTPException(status_code=404, detail="Task not found or expired")
    
    return json.loads(status_raw)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))