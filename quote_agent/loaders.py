"""Turn uploaded files into something the LLM can read: text, or page images for scans."""
from __future__ import annotations

import base64
import email
import io
import unicodedata
from dataclasses import dataclass, field
from email import policy
from pathlib import Path

MIN_TEXT_CHARS = 80  # below this, a PDF is treated as scanned
MAX_PAGES = 5


@dataclass
class LoadedDoc:
    name: str
    text: str = ""
    images: list[str] = field(default_factory=list)  # base64 PNGs
    mime: str = "image/png"


def _pdf(name: str, data: bytes) -> LoadedDoc:
    # pdfium (Chrome's PDF engine) keeps numbers and Latin text inside Arabic lines;
    # pypdf is only a fallback because it drops them in many Arabic PDFs.
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(data)
    try:
        text = "\n".join(pdf[i].get_textpage().get_text_range() for i in range(min(len(pdf), MAX_PAGES)))
    except Exception:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        text = "\n".join((p.extract_text() or "") for p in reader.pages[:MAX_PAGES])
    # Arabic PDFs often extract as presentation forms (e.g. U+FEB7); NFKC maps them to normal letters.
    text = unicodedata.normalize("NFKC", text).replace("\r", "").strip()
    if len(text) >= MIN_TEXT_CHARS:
        return LoadedDoc(name=name, text=text)

    # Scanned PDF: render pages to images for a vision-capable model.
    images = []
    for i in range(min(len(pdf), MAX_PAGES)):
        pil = pdf[i].render(scale=2).to_pil()
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        images.append(base64.b64encode(buf.getvalue()).decode())
    return LoadedDoc(name=name, text=text, images=images)


def _eml(name: str, data: bytes) -> LoadedDoc:
    msg = email.message_from_bytes(data, policy=policy.default)
    body = msg.get_body(preferencelist=("plain", "html"))
    content = body.get_content() if body else ""
    header = f"From: {msg.get('From', '')}\nSubject: {msg.get('Subject', '')}\nDate: {msg.get('Date', '')}\n\n"
    return LoadedDoc(name=name, text=header + content)


def load_bytes(name: str, data: bytes) -> LoadedDoc:
    ext = Path(name).suffix.lower()
    if ext == ".pdf":
        return _pdf(name, data)
    if ext == ".eml":
        return _eml(name, data)
    if ext in {".png", ".jpg", ".jpeg", ".webp"}:
        mime = "image/jpeg" if ext in {".jpg", ".jpeg"} else f"image/{ext[1:]}"
        return LoadedDoc(name=name, images=[base64.b64encode(data).decode()], mime=mime)
    if ext in {".txt", ".md", ".csv"}:
        return LoadedDoc(name=name, text=data.decode("utf-8", errors="replace"))
    raise ValueError(f"Unsupported file type: {name}")


def load_path(path: str | Path) -> LoadedDoc:
    p = Path(path)
    return load_bytes(p.name, p.read_bytes())
