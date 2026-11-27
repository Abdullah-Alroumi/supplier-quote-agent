"""Harder test set: 4 packaging quotes (3 items each) in 4 different formats.

    1  Najd Packaging   - English PDF, SAR excl. VAT, delivery fee, no warranty stated
    2  Al-Wafa Cartons  - SCANNED image (PNG) + scanned PDF, Arabic, prices incl. VAT
    3  Al-Sahel Pack    - Arabic text PDF, excl. VAT, 50% advance, 7-day validity
    4  EuroPack GmbH    - English email in EUR, MISSING the pallets item (incomplete quote)
"""
from email.message import EmailMessage
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUT = Path(__file__).resolve().parent.parent / "samples_set2"
OUT.mkdir(exist_ok=True)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
pdfmetrics.registerFont(TTFont("DejaVu", FONT))
ss = getSampleStyleSheet()


def ar(text: str) -> str:
    return get_display(arabic_reshaper.reshape(text))


def table_style():
    return TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "DejaVu"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d4a3e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ])


# ---------- 1. English PDF ----------
doc = SimpleDocTemplate(str(OUT / "1_najd_packaging_EN.pdf"), pagesize=A4)
story = [Paragraph("Najd Packaging Solutions", ss["Title"]),
         Paragraph("Riyadh 2nd Industrial City | Quote NPS-Q-5521 | 21 Nov 2026", ss["Normal"]),
         Spacer(1, 14)]
t = Table([["Item", "Qty", "Unit price (SAR)", "Amount (SAR)"],
           ["Double-wall carton box 60x40x40", "5,000 pcs", "3.20", "16,000.00"],
           ["Stretch film 23 micron, 500mm", "200 rolls", "38.00", "7,600.00"],
           ["Wooden pallet 120x100 (heat treated)", "300 pcs", "45.00", "13,500.00"],
           ["", "", "Subtotal", "37,100.00"],
           ["", "", "Delivery charge", "750.00"],
           ["", "", "VAT 15%", "5,677.50"],
           ["", "", "TOTAL", "43,527.50"]], colWidths=[200, 70, 110, 100])
t.setStyle(table_style())
story += [t, Spacer(1, 14)]
for line in ["Prices exclude VAT.", "Delivery within 5 days of PO, Riyadh warehouse.",
             "Payment terms: Net 45 days.", "Quotation valid for 20 days."]:
    story.append(Paragraph("- " + line, ss["Normal"]))
doc.build(story)


# ---------- 2. Scanned Arabic quote (image + image-only PDF) ----------
W, H = 1240, 1754
img = Image.new("RGB", (W, H), (250, 248, 240))
d = ImageDraw.Draw(img)
big, mid = ImageFont.truetype(FONT, 46), ImageFont.truetype(FONT, 30)


def rtl(y, text, font=mid, x_right=W - 90):
    # Pillow with libraqm shapes Arabic itself; without it, pre-shape with reshaper + bidi.
    from PIL import features
    if features.check("raqm"):
        kw = {"direction": "rtl", "language": "ar"}
        w = d.textlength(text, font=font, **kw)
        d.text((x_right - w, y), text, fill=(30, 30, 30), font=font, **kw)
    else:
        s = ar(text)
        w = d.textlength(s, font=font)
        d.text((x_right - w, y), s, fill=(30, 30, 30), font=font)


rtl(90, "مصنع الوفاء للكرتون", big)
rtl(160, "المنطقة الصناعية - الدمام | عرض سعر رقم 3390")
rtl(205, "التاريخ: 22/11/2026")
rows = [("الصنف", "الكمية", "سعر الوحدة", "الإجمالي"),
        ("كرتون مزدوج 60x40x40", "5000", "3.50", "17,500"),
        ("رول تغليف استرتش", "200", "42.00", "8,400"),
        ("طبلية خشب 120x100", "300", "48.00", "14,400")]
cols = [1150, 640, 450, 260]
y = 300
for r in rows:
    for txt, xr in zip(r, cols):
        rtl(y, txt, x_right=xr)
    d.line((90, y + 50, W - 90, y + 50), fill=(120, 120, 120), width=2)
    y += 75
y += 30
for line in ["الإجمالي: 40,300 ريال (الأسعار شاملة ضريبة القيمة المضافة)",
             "التوصيل: مجاني داخل المنطقة الشرقية والرياض",
             "مدة التوريد: أسبوعين من تاريخ أمر الشراء",
             "الدفع: آجل 30 يوماً",
             "الضمان: 3 أشهر ضد عيوب التصنيع",
             "صلاحية العرض: 15 يوماً"]:
    rtl(y, line)
    y += 60
d.ellipse((120, y + 40, 360, y + 280), outline=(40, 70, 160), width=6)  # fake stamp
d.text((165, y + 140), "AL-WAFA", fill=(40, 70, 160), font=mid)
scan = img.rotate(0.8, expand=True, fillcolor=(235, 233, 225)).filter(ImageFilter.GaussianBlur(0.7)).convert("L")
scan.save(OUT / "2_alwafa_cartons_AR_scanned.png")
scan.convert("RGB").save(OUT / "2b_alwafa_cartons_AR_scanned.pdf")  # image-only PDF -> vision path


# ---------- 3. Arabic text PDF ----------
arstyle = ParagraphStyle("ar", fontName="DejaVu", fontSize=11, alignment=2, leading=18)
artitle = ParagraphStyle("art", parent=arstyle, fontSize=18, leading=26)
doc = SimpleDocTemplate(str(OUT / "3_alsahel_pack_AR.pdf"), pagesize=A4)
story = [Paragraph(ar("شركة الساحل للتغليف"), artitle),
         Paragraph(ar("جدة - عرض سعر رقم SP-2026-087 - بتاريخ 20/11/2026"), arstyle), Spacer(1, 14)]
t = Table([[ar("الإجمالي"), ar("سعر الوحدة"), ar("الكمية"), ar("الصنف")],
           ["15,250.00", "3.05", "5000", ar("كرتون مزدوج 60x40x40")],
           ["7,200.00", "36.00", "200", ar("رول استرتش 23 ميكرون")],
           ["13,200.00", "44.00", "300", ar("طبلية خشب معالجة حرارياً")],
           ["35,650.00", "", "", ar("المجموع قبل الضريبة")],
           ["1,200.00", "", "", ar("رسوم النقل")]], colWidths=[100, 90, 70, 220])
t.setStyle(table_style())
story += [t, Spacer(1, 14)]
for line in ["الأسعار لا تشمل ضريبة القيمة المضافة 15%",
             "مدة التوريد: 3 أسابيع",
             "طريقة الدفع: 50% دفعة مقدمة و50% عند الاستلام",
             "الضمان: 6 أشهر",
             "صلاحية العرض: 7 أيام فقط",
             "الأسعار قابلة للتغيير حسب أسعار المواد الخام"]:
    story.append(Paragraph(ar("- " + line), arstyle))
doc.build(story)


# ---------- 4. English email in EUR, incomplete ----------
msg = EmailMessage()
msg["From"] = "Export Sales <export@europack.example>"
msg["To"] = "procurement@yourcompany.example"
msg["Subject"] = "RE: RFQ packaging materials - EuroPack offer"
msg["Date"] = "Fri, 20 Nov 2026 14:05:00 +0100"
msg.set_content("""Dear Procurement Team,

Thank you for your RFQ. Please find our best offer below:

- Double-wall carton 60x40x40: 5,000 pcs x EUR 0.78 = EUR 3,900.00
- Stretch film 23mic 500mm: 200 rolls x EUR 8.50 = EUR 1,700.00

Unfortunately we do not supply wooden pallets.

Sea freight to Dammam: EUR 650.00
Prices are ex-VAT; Saudi VAT and customs are for the buyer's account.
Lead time: 6 weeks from order confirmation.
Payment: 30 days after Bill of Lading.
Warranty: 12 months.
Validity: 30 days.

Best regards,
Klaus Weber
EuroPack GmbH
""")
(OUT / "4_europack_EN_EUR.eml").write_bytes(bytes(msg))
print("Written to", OUT)
