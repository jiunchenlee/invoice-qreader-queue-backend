from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class InvoiceMetadata(BaseModel):
    """發票 Metadata 模型"""
    invoice_number: str = Field(..., description="發票號碼 (10碼)")
    invoice_date: str = Field(..., description="發票日期 YYYMMDD")
    invoice_date_formatted: str = Field(..., description="格式化日期 YYYY-MM-DD")
    random_code: str = Field(..., description="隨機碼 (4碼)")
    sales_amount: int = Field(..., description="銷售額 (10進制)")
    total_amount: int = Field(..., description="總計額 (10進制)")
    buyer_tax_id: str = Field(..., description="買方統編")
    seller_tax_id: str = Field(..., description="賣方統編")
    aes_encrypted: str = Field(..., description="AES 加密字串")
    image_url: str = Field(..., description="圖片 URL")
    is_duplicate: bool = Field(default=False, description="是否為重複上傳")
    created_at: datetime = Field(default_factory=datetime.now)

class MultiUploadResponse(BaseModel):
    """API 回傳模型 (多張發票)"""
    success: bool
    data: Optional[list[InvoiceMetadata]] = None
    error: Optional[dict] = None

class ErrorResponse(BaseModel):
    """錯誤回傳模型"""
    code: str
    message: str
    details: Optional[str] = None
