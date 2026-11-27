"""Generate 3 demo quotes for 20 tons of HDPE granules.

The demo story: the Arabic email has the HIGHEST price per ton (5,300 SAR) but it already
includes VAT and free delivery, so after normalisation it is actually the CHEAPEST offer.
    A  Gulf Polymers (PDF, SAR, excl. VAT)            -> 111,550.00 SAR
    B  Asia Plastics (PDF, USD + freight, excl. VAT)  -> 115,143.75 SAR
    C  Al-Sharq Supply (Arabic email, incl. VAT)      -> 106,000.00 SAR
"""
from email.message import EmailMessage
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUT = Path(__file__).resolve().parent.parent / "samples"
OUT.mkdir(exist_ok=True)
ss = getSampleStyleSheet()


def pdf(name, header, rows, totals, terms):
    doc = SimpleDocTemplate(str(OUT / name), pagesize=A4)
    story = [Paragraph(h, ss["Title"] if i == 0 else ss["Normal"]) for i, h in enumerate(header)]
    story.append(Spacer(1, 16))
    t = Table([["Description", "Qty", "Unit", "Unit price", "Total"]] + rows + totals,
              colWidths=[200, 50, 50, 90, 100])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3b57")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
    ]))
    story += [t, Spacer(1, 16), Paragraph("<b>Terms &amp; Conditions</b>", ss["Heading3"])]
    story += [Paragraph(f"- {x}", ss["Normal"]) for x in terms]
    doc.build(story)


pdf(
    "quote_A_gulf_polymers.pdf",
    ["Gulf Polymers Trading Co.", "Jeddah Industrial City, Phase 3 - CR 4030000000",
     "QUOTATION No. GPT-2026-1184 &nbsp;&nbsp; Date: 20/11/2026", "Attn: Procurement Department"],
    [["HDPE Granules - Blow Moulding Grade", "20", "Ton", "4,850.00", "97,000.00"]],
    [["", "", "", "Subtotal (SAR)", "97,000.00"],
     ["", "", "", "Delivery", "Included"],
     ["", "", "", "VAT 15%", "14,550.00"],
     ["", "", "", "Grand Total (SAR)", "111,550.00"]],
    ["All prices are in Saudi Riyals and exclude VAT (VAT shown separately).",
     "Delivery: within 7 days from PO to your warehouse.",
     "Payment: 30 days from invoice date.",
     "Quality guarantee: 6 months against manufacturing defects.",
     "Offer valid for 15 days.",
     "Unloading at site is the buyer's responsibility."],
)

pdf(
    "quote_B_asia_plastics.pdf",
    ["ASIA PLASTICS RAW MATERIALS LTD.", "Export Department - Shanghai",
     "PROFORMA INVOICE / QUOTE: APR-77215 &nbsp;&nbsp; Date: 18-Nov-2026", "To: Purchasing Manager, KSA"],
    [["HDPE Granules (Blow Moulding)", "20", "MT", "USD 1,240", "USD 24,800"]],
    [["", "", "", "Sea freight to Jeddah", "USD 1,900"],
     ["", "", "", "TOTAL (USD)", "USD 26,700"]],
    ["Prices in US Dollars, CFR Jeddah. Saudi VAT and customs clearance not included.",
     "Lead time: 5 weeks after receipt of payment.",
     "Payment: 100% T/T in advance.",
     "No warranty after shipment; claims within 7 days of arrival only.",
     "Quotation valid 10 days. Prices subject to resin market changes."],
)

msg = EmailMessage()
msg["From"] = "مؤسسة الشرق للتوريد <sales@alsharq-supply.example>"
msg["To"] = "procurement@yourcompany.example"
msg["Subject"] = "عرض سعر - حبيبات بولي إيثيلين عالي الكثافة HDPE"
msg["Date"] = "Thu, 19 Nov 2026 10:12:00 +0300"
msg.set_content("""السلام عليكم ورحمة الله وبركاته،

بالإشارة إلى طلبكم، يسرنا تقديم عرض السعر التالي:

الصنف: حبيبات HDPE درجة النفخ
الكمية: 20 طن
سعر الطن: 5,300 ريال (السعر شامل ضريبة القيمة المضافة 15%)
الإجمالي: 106,000 ريال شامل الضريبة

التوصيل: مجاني إلى مستودعكم خلال 10 أيام عمل من تاريخ أمر الشراء
الدفع: آجل 60 يوماً من تاريخ الفاتورة
الضمان: ضمان جودة لمدة 12 شهراً
صلاحية العرض: 30 يوماً

نتطلع لخدمتكم،
قسم المبيعات - مؤسسة الشرق للتوريد
""", charset="utf-8")
(OUT / "quote_C_alsharq_email.eml").write_bytes(bytes(msg))
print("Samples written to", OUT)
