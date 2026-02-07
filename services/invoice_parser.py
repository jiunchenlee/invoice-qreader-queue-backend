from datetime import datetime

class InvoiceParser:
    @staticmethod
    def parse_qr_code(qr_data: str) -> dict:
        if len(qr_data) != 77: raise ValueError(f"QR Code 長度錯誤: {len(qr_data)}")
        roc_date = qr_data[10:17]
        year = int(roc_date[0:3]) + 1911
        formatted_date = f"{year}-{roc_date[3:5]}-{roc_date[5:7]}"
        return {
            "invoice_number": qr_data[0:10],
            "invoice_date": roc_date,
            "invoice_date_formatted": formatted_date,
            "random_code": qr_data[17:21],
            "sales_amount": int(qr_data[21:29], 16),
            "total_amount": int(qr_data[29:37], 16),
            "buyer_tax_id": qr_data[37:45],
            "seller_tax_id": qr_data[45:53],
            "aes_encrypted": qr_data[53:77]
        }
