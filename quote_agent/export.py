"""Comparison table -> DataFrame / Excel."""
from __future__ import annotations

import io

import pandas as pd

from .schemas import QuoteRow

LABELS = {
    "ar": {
        "rank": "الترتيب", "supplier_name": "المورد", "total_sar": "الإجمالي (ريال شامل الضريبة)",
        "subtotal_sar": "قبل الضريبة", "shipping_fees_sar": "شحن ورسوم", "vat_sar": "الضريبة",
        "currency": "عملة العرض", "delivery_days": "التوريد (يوم)", "credit_days": "مهلة الدفع (يوم)",
        "warranty_months": "الضمان (شهر)", "validity_days": "صلاحية العرض (يوم)", "total_score": "التقييم /100",
        "warnings": "تنبيهات", "source_file": "الملف",
    },
    "en": {
        "rank": "Rank", "supplier_name": "Supplier", "total_sar": "Total (SAR incl. VAT)",
        "subtotal_sar": "Before VAT", "shipping_fees_sar": "Shipping & fees", "vat_sar": "VAT",
        "currency": "Quote currency", "delivery_days": "Delivery (days)", "credit_days": "Credit (days)",
        "warranty_months": "Warranty (months)", "validity_days": "Validity (days)", "total_score": "Score /100",
        "warnings": "Warnings", "source_file": "File",
    },
}


def to_dataframe(rows: list[QuoteRow], language: str = "ar") -> pd.DataFrame:
    labels = LABELS.get(language, LABELS["en"])
    data = []
    for r in rows:
        d = r.model_dump()
        d["warnings"] = " | ".join(r.warnings)
        data.append({labels[k]: d[k] for k in labels})
    return pd.DataFrame(data)


def to_excel(rows: list[QuoteRow], language: str = "ar") -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        to_dataframe(rows, language).to_excel(xw, index=False, sheet_name="Comparison")
        ws = xw.sheets["Comparison"]
        ws.sheet_view.rightToLeft = language == "ar"
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = 22
    return buf.getvalue()
