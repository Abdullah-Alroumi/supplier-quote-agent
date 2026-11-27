"""Dashboard styling: CSS, line icons (Lucide, MIT) and small HTML components for app.py."""
from __future__ import annotations

import html
import re

ACCENT = "#198754"

_ICON_PATHS = {
    "scale": '<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>',
    "trophy": '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/>',
    "wallet": '<path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/>',
    "trending-down": '<polyline points="22 17 13.5 8.5 8.5 13.5 2 7"/><polyline points="16 17 22 17 22 11"/>',
    "arrow-up-right": '<path d="M7 7h10v10"/><path d="M7 17 17 7"/>',
    "files": '<path d="M20 7h-3a2 2 0 0 1-2-2V2"/><path d="M9 18a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h7l4 4v10a2 2 0 0 1-2 2Z"/><path d="M3 7.6v12.8A1.6 1.6 0 0 0 4.6 22h9.8"/>',
    "chart": '<path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>',
    "table": '<path d="M12 3v18"/><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M3 15h18"/>',
    "check": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "tag": '<path d="M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8.704 8.704a2.426 2.426 0 0 0 3.42 0l6.58-6.58a2.426 2.426 0 0 0 0-3.42z"/><circle cx="7.5" cy="7.5" r="1"/>',
    "mail": '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
    "bulb": '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/>',
}


def icon(name: str, size: int = 18, color: str = "currentColor") -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
            f'fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
            f'style="flex-shrink:0">{_ICON_PATHS[name]}</svg>')


def css(rtl: bool) -> str:
    direction = """
    [data-testid="stApp"], [data-testid="stSidebar"], [data-testid="stMain"] { direction: rtl; }
    [data-testid="stMarkdownContainer"], .stAlert, textarea, input, label { text-align: right; }
    [data-testid="stSlider"], [data-testid="stVegaLiteChart"] { direction: ltr; }
    """ if rtl else ""
    return f"""<style>
    {direction}
    .block-container {{ padding-top: 3.2rem; max-width: 1280px; }}
    .qa-card {{ border: 1px solid rgba(128,128,128,.22); border-radius: 12px; padding: 18px 20px;
               background: rgba(128,128,128,.045); height: 100%; }}
    .qa-head {{ display:flex; align-items:center; gap:10px; font-weight:600; font-size:16px; margin-bottom:12px; }}
    .qa-head .qa-ic {{ display:flex; align-items:center; justify-content:center; width:32px; height:32px;
                      border-radius:8px; background: rgba(25,135,84,.14); color:{ACCENT}; }}
    .qa-kpis {{ display:grid; grid-template-columns: 1.4fr 1fr 1fr 1fr; gap:14px; margin: 18px 0 16px; }}
    @media (max-width: 900px) {{ .qa-kpis {{ grid-template-columns: 1fr 1fr; }} }}
    .qa-kpi {{ border:1px solid rgba(128,128,128,.22); border-radius:12px; padding:16px 18px;
              background: rgba(128,128,128,.045); }}
    .qa-kpi.win {{ background: linear-gradient(135deg,#0f5132,{ACCENT}); border:none; color:#fff; }}
    .qa-kpi .lbl {{ display:flex; align-items:center; gap:8px; font-size:13px; opacity:.75; }}
    .qa-kpi .val {{ font-size:24px; font-weight:700; margin-top:8px; line-height:1.25; }}
    .qa-kpi .val, .qa-num {{ unicode-bidi: plaintext; }}
    .qa-kpi .sub {{ font-size:12px; opacity:.7; margin-top:4px; }}
    .qa-title {{ display:flex; align-items:center; gap:14px; margin-bottom:6px; }}
    .qa-title .logo {{ display:flex; align-items:center; justify-content:center; width:48px; height:48px;
                      border-radius:12px; background:{ACCENT}; color:#fff; }}
    .qa-title h1 {{ font-size:28px; margin:0; padding:0; }}
    .qa-title p {{ margin:2px 0 0; opacity:.65; font-size:14px; }}
    table.qa-table {{ width:100%; border-collapse:collapse; font-size:14px; }}
    .qa-table th {{ text-align:start; font-weight:600; font-size:12.5px; opacity:.7; padding:10px 10px;
                   border-bottom:1px solid rgba(128,128,128,.25); white-space:nowrap; }}
    .qa-table td {{ padding:12px 10px; border-bottom:1px solid rgba(128,128,128,.13); vertical-align:top; }}
    .qa-table tr.win td {{ background: rgba(25,135,84,.10); }}
    .qa-table tr.inc td {{ opacity:.6; }}
    .qa-num {{ font-variant-numeric: tabular-nums; white-space:nowrap; }}
    .qa-small {{ font-size:12px; opacity:.65; margin-top:3px; }}
    .qa-badge {{ display:inline-block; font-size:11px; font-weight:600; padding:2px 8px; border-radius:999px;
                margin-inline-start:6px; vertical-align:middle; }}
    .qa-badge.win {{ background: rgba(25,135,84,.18); color:{ACCENT}; }}
    .qa-badge.inc {{ background: rgba(220,53,69,.15); color:#dc3545; }}
    .qa-bar {{ height:6px; border-radius:3px; background: rgba(128,128,128,.2); margin-top:6px; width:80px; }}
    .qa-bar > div {{ height:100%; border-radius:3px; background:{ACCENT}; }}
    .qa-warn {{ font-size:12px; color:#d9822b; margin-top:2px; }}
    .qa-list div {{ display:flex; gap:8px; align-items:flex-start; margin:8px 0; line-height:1.55; }}
    .qa-list svg {{ margin-top:4px; }}
    </style>"""


def esc(x) -> str:
    return html.escape(str(x))


def card(title: str, ic: str, body: str) -> str:
    return (f'<div class="qa-card"><div class="qa-head"><span class="qa-ic">{icon(ic)}</span>{esc(title)}</div>'
            f'{body}</div>')


def card_head(title: str, ic: str) -> str:
    """Header only - for native Streamlit content (charts, inputs) placed inside st.container(border=True)."""
    return f'<div class="qa-head"><span class="qa-ic">{icon(ic)}</span>{esc(title)}</div>'


def kpi(label: str, value: str, ic: str, sub: str = "", win: bool = False) -> str:
    return (f'<div class="qa-kpi{" win" if win else ""}"><div class="lbl">{icon(ic, 16)}{esc(label)}</div>'
            f'<div class="val">{esc(value)}</div>{f"<div class=sub>{esc(sub)}</div>" if sub else ""}</div>')


def bullet_list(items: list[str], ic: str, color: str) -> str:
    rows = "".join(f"<div>{icon(ic, 15, color)}<span>{esc(x)}</span></div>" for x in items) or "<div>—</div>"
    return f'<div class="qa-list">{rows}</div>'


_AR_WARN = [
    (r"^INCOMPLETE: quotes (\d+) of (\d+) items.*", r"عرض ناقص: يغطي \1 من \2 أصناف، ولا يُقارن إجماليه بغيره"),
    (r"^CHECK NUMBERS: .*", "الأرقام غير متطابقة مع الإجمالي المكتوب في العرض، راجع الملف"),
    (r"^Missing delivery time$", "مدة التوريد غير مذكورة"),
    (r"^Missing payment terms$", "شروط الدفع غير مذكورة"),
    (r"^Missing warranty$", "الضمان غير مذكور"),
    (r"^Missing offer validity$", "صلاحية العرض غير مذكورة"),
    (r"^Unknown currency (\w+); treated as SAR$", r"عملة غير معروفة (\1) واعتُبرت ريالاً"),
]


def warn_text(w: str, lang: str) -> str:
    if lang != "ar":
        return w
    for pat, rep in _AR_WARN:
        if re.match(pat, w):
            return re.sub(pat, rep, w)
    return w
