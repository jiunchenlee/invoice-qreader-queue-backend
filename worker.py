import os
import json
import requests
import tempfile
import time
from redis import Redis
from services.qr_processor import QRProcessor
from services.invoice_parser import InvoiceParser
from services.supabase_client import SupabaseService

# 初始化環境
REDIS_URL = os.getenv("REDIS_URL", "redis://default:TjVSiTlscOkTrhUMXqyFmcHpPaFhDRsW@redis.railway.internal:6379")
redis_conn = Redis.from_url(REDIS_URL)
qr_processor = QRProcessor()
supabase_service = SupabaseService()

def process_task(task_data):
    """
    執行辨識任務：下載圖片 -> 辨識 -> 存入 DB -> 更新 Redis
    """
    task_id = task_data.get("task_id")
    image_urls = task_data.get("image_urls", [])
    total = len(image_urls)
    all_results = []

    print(f"🚀 [Worker] 開始處理任務 {task_id}, 共 {total} 張圖片")

    for idx, url in enumerate(image_urls):
        try:
            # 1. 更新進度 (0-100)
            progress = int(((idx + 1) / total) * 100)
            status_data = {
                "status": "processing",
                "current": idx + 1,
                "total": total,
                "progress": progress,
                "message": f"正在處理第 {idx+1}/{total} 張圖片"
            }
            redis_conn.setex(f"task_status:{task_id}", 3600, json.dumps(status_data))

            # 2. 下載圖片到暫存
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                continue

            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(response.content)
                temp_path = tmp.name

            # 3. 執行辨識
            detections, decoded_texts = qr_processor.detect_and_decode(temp_path)
            # 使用多張辨識的分組邏輯
            groups = qr_processor.group_qrs_by_invoice(detections, decoded_texts)

            for g in groups:
                try:
                    m = InvoiceParser.parse_qr_code(g["left_data"])
                    m["source"] = "Queue"
                    # 檢查重複並儲存
                    m["is_duplicate"] = supabase_service.check_duplicate(m["invoice_number"])
                    # 直接使用傳入的 Supabase URL 存入 DB
                    supabase_service.save_invoice(m, url)
                    all_results.append(m)
                except Exception as parse_err:
                    print(f"解析失敗: {parse_err}")
                    continue

            # 清理暫存
            if os.path.exists(temp_path):
                os.unlink(temp_path)

        except Exception as e:
            print(f"❌ [Worker] 處理圖片時發生錯誤: {url}, Error: {e}")
            continue

    # 4. 任務完成
    final_status = {
        "status": "completed",
        "current": total,
        "total": total,
        "progress": 100,
        "results": all_results
    }
    redis_conn.setex(f"task_status:{task_id}", 3600, json.dumps(final_status))
    print(f"✅ [Worker] 任務 {task_id} 處理完成，共辨識出 {len(all_results)} 張發票")

def main():
    print("👷 Worker 已啟動，正在監聽任務佇列...")
    while True:
        # 從 Redis 列表左側取得任務 (Blocking POP)
        task_raw = redis_conn.blpop("invoice_tasks", timeout=30)
        if task_raw:
            try:
                task_data = json.loads(task_raw[1])
                process_task(task_data)
            except Exception as e:
                print(f"❌ [Worker] 執行任務失敗: {e}")
        else:
            # 沒任務時小睡一下
            time.sleep(1)

if __name__ == "__main__":
    main()