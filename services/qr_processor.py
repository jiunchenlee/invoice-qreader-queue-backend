from qreader import QReader
import cv2
import numpy as np
from typing import Tuple, Optional

class QRProcessor:
    def __init__(self):
        self.qreader = QReader()
    
    def detect_and_decode(self, image_path: str) -> Tuple[list, list]:
        image = cv2.imread(image_path)
        if image is None: raise ValueError("無法讀取圖片檔案")
        # 使用與 API 1 一致的原始調用
        decoded_texts, detections = self.qreader.detect_and_decode(image=image, return_detections=True)
        return detections, decoded_texts
    
    def group_qrs_by_invoice(self, detections: list, decoded_texts: list) -> list:
        if not decoded_texts: return []
        invoices = []
        for text in decoded_texts:
            if not text: continue
            # 寬容模式：只要有內容就視為潛在發票，由 Parser 去處理異常
            invoices.append({"left_data": text[:77], "right_data": ""})
        return invoices
