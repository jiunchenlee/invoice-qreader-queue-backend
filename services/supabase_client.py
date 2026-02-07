import os
from supabase import create_client, Client
from datetime import datetime
import uuid

class SupabaseService:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_KEY")
        self.bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "invoice-images")
        self.client = create_client(self.url, self.key) if self.url and self.key else None

    def upload_image(self, file_path: str, file_name: str) -> str:
        if not self.client: return ""
        unique_name = f"{datetime.now().strftime('%Y/%m')}/{uuid.uuid4()}-{file_name}"
        with open(file_path, 'rb') as f:
            self.client.storage.from_(self.bucket).upload(path=unique_name, file=f.read(), file_options={"content-type": "image/jpeg"})
        return self.client.storage.from_(self.bucket).get_public_url(unique_name)

    def check_duplicate(self, invoice_number: str) -> bool:
        if not self.client: return False
        try:
            res = self.client.table("invoices").select("invoice_number").eq("invoice_number", invoice_number).execute()
            return len(res.data) > 0
        except: return False

    def save_invoice(self, metadata: dict, image_url: str) -> dict:
        if not self.client: return {}
        
        whitelist = [
            "invoice_number", "invoice_date", "invoice_date_formatted",
            "random_code", "sales_amount", "total_amount",
            "buyer_tax_id", "seller_tax_id", "aes_encrypted",
            "is_duplicate", "source"
        ]
        db_payload = { k: v for k, v in metadata.items() if k in whitelist }
        db_payload["image_url"] = image_url
        db_payload["created_at"] = datetime.now().isoformat()
        
        try:
            res = self.client.table("invoices").insert(db_payload).execute()
            return res.data[0] if res.data else {}
        except Exception as e:
            print(f"Database Save Error: {e}")
            return {}