"""Streamlit UI.  Run:  streamlit run app.py"""
import os

import altair as alt
import pandas as pd
import streamlit as st

import ui

# On Streamlit Community Cloud the key lives in the app's Secrets, not in a .env file.
try:
    for _k in ("GOOGLE_API_KEY", "ANTHROPIC_API_KEY", "QUOTE_AGENT_MODEL"):
        if _k in st.secrets:
            os.environ.setdefault(_k, str(st.secrets[_k]))
except Exception:  # no secrets file when running locally - .env is used instead
    pass

from quote_agent.export import to_excel
from quote_agent.graph import run
from quote_agent.loaders import load_bytes
from quote_agent.scoring import DEFAULT_FX

T = {
    "ar": {
        "title": "وكيل مقارنة عروض الموردين",
        "sub": "ارفع عروض الأسعار (PDF أو صورة أو إيميل) واحصل على مقارنة وتوصية خلال دقيقة.",
        "upload": "عروض الأسعار (2 إلى 6 ملفات)", "run": "قارن العروض", "weights": "أوزان التقييم",
        "price": "السعر", "delivery": "سرعة التوريد", "payment": "مهلة الدفع", "warranty": "الضمان",
        "fx": "أسعار الصرف (ريال لكل وحدة)", "need2": "ارفع عرضين على الأقل.",
        "working": "الوكيل يقرأ العروض ويقارنها...", "table": "جدول المقارنة",
        "best": "التوصية", "reasons": "الأسباب", "risks": "مخاطر وتنبيهات",
        "nego": "نقاط للتفاوض", "email": "مسودة رد للمورد", "excel": "تحميل Excel",
        "saving": "التوفير مقارنة بأغلى عرض", "errors": "ملفات لم تُقرأ",
        "real_total": "التكلفة الحقيقية (شامل الضريبة والشحن)", "quotes_read": "عروض تمت قراءتها",
        "chart": "التكلفة الحقيقية لكل عرض", "winner": "الأفضل", "incomplete": "عرض ناقص", "other": "باقي العروض",
        "why": "ملخص القرار", "vs_cheapest": "الفرق عن الأرخص",
        "cheapest_is": "أرخص عرض: {name}", "of_total": "شامل الضريبة والشحن", "incl": "منها شحن {s} · ضريبة {v}",
        "cols": ["#", "المورد", "التكلفة الحقيقية", "التوريد", "مهلة الدفع", "الضمان", "الصلاحية", "التقييم"],
        "days": "يوم", "months": "شهر", "settings": "الإعدادات", "model": "الموديل", "subject": "الموضوع",
        "body": "نص الرسالة", "warned": "{n} تنبيه",
    },
    "en": {
        "title": "Supplier Quote Comparison Agent",
        "sub": "Upload quotes (PDF, image or email) and get a comparison and recommendation in a minute.",
        "upload": "Supplier quotes (2-6 files)", "run": "Compare quotes", "weights": "Scoring weights",
        "price": "Price", "delivery": "Delivery speed", "payment": "Credit days", "warranty": "Warranty",
        "fx": "FX rates (SAR per unit)", "need2": "Upload at least two quotes.",
        "working": "The agent is reading and comparing the quotes...", "table": "Comparison",
        "best": "Recommendation", "reasons": "Why", "risks": "Risks & warnings",
        "nego": "Negotiation points", "email": "Draft reply to supplier", "excel": "Download Excel",
        "saving": "Saving vs. most expensive", "errors": "Files that could not be read",
        "real_total": "Real cost (incl. VAT & shipping)", "quotes_read": "Quotes read",
        "chart": "Real cost per quote", "winner": "Best", "incomplete": "Incomplete", "other": "Other quotes",
        "why": "Decision summary", "vs_cheapest": "Gap to cheapest",
        "cheapest_is": "Cheapest: {name}", "of_total": "incl. VAT & shipping", "incl": "shipping {s} · VAT {v}",
        "cols": ["#", "Supplier", "Real cost", "Delivery", "Credit", "Warranty", "Validity", "Score"],
        "days": "days", "months": "mo", "settings": "Settings", "model": "Model", "subject": "Subject",
        "body": "Message", "warned": "{n} warnings",
    },
}

st.set_page_config(page_title="Quote Agent", page_icon=":material/balance:", layout="wide")

lang = st.sidebar.radio("Language / اللغة", ["ar", "en"], format_func=lambda x: "العربية" if x == "ar" else "English")
t = T[lang]
st.markdown(ui.css(rtl=lang == "ar"), unsafe_allow_html=True)

st.sidebar.subheader(t["weights"])
weights = {k: st.sidebar.slider(t[k], 0, 100, v, 5)
           for k, v in {"price": 50, "delivery": 20, "payment": 15, "warranty": 15}.items()}
with st.sidebar.expander(t["fx"], icon=":material/currency_exchange:"):
    fx = {c: st.number_input(c, value=float(r), step=0.01, format="%.3f") for c, r in DEFAULT_FX.items() if c != "SAR"}
with st.sidebar.expander(t["settings"], icon=":material/settings:"):
    model = st.text_input(t["model"], os.getenv("QUOTE_AGENT_MODEL", "google_genai:gemini-3.5-flash"))

st.markdown(f'''<div class="qa-title"><div class="logo">{ui.icon("scale", 26)}</div>
<div><h1>{ui.esc(t["title"])}</h1><p>{ui.esc(t["sub"])}</p></div></div>''', unsafe_allow_html=True)

with st.container(border=True):
    files = st.file_uploader(t["upload"], accept_multiple_files=True,
                             type=["pdf", "png", "jpg", "jpeg", "webp", "eml", "txt"])
    clicked = st.button(t["run"], type="primary", icon=":material/compare_arrows:")

if clicked:
    if not files or len(files) < 2:
        st.warning(t["need2"], icon=":material/info:")
        st.stop()
    with st.spinner(t["working"]):
        docs = [load_bytes(f.name, f.getvalue()) for f in files]
        st.session_state.result = run(docs, language=lang, weights=weights, fx=fx, model=model)
        st.session_state.lang = lang

res = st.session_state.get("result")
if res:
    rlang = st.session_state.get("lang", lang)
    if res.get("errors"):
        st.error(t["errors"] + ":\n\n" + "\n\n".join(res["errors"]), icon=":material/error:")
    rows = res.get("rows") or []
    if rows:
        def is_inc(r):
            return any(w.startswith("INCOMPLETE") for w in r.warnings)

        complete = [r for r in rows if not is_inc(r)] or rows
        best = rows[0]
        cheapest = min(complete, key=lambda r: r.total_sar)
        n_warn = sum(len(r.warnings) for r in rows)

        if cheapest is best:
            third = ui.kpi(t["saving"], f"{max(r.total_sar for r in complete) - best.total_sar:,.2f} SAR",
                           "trending-down")
        else:
            third = ui.kpi(t["vs_cheapest"], f"+{best.total_sar - cheapest.total_sar:,.2f} SAR", "arrow-up-right",
                           sub=t["cheapest_is"].format(name=cheapest.supplier_name))
        st.markdown(
            '<div class="qa-kpis">'
            + ui.kpi(t["best"], best.supplier_name, "trophy", win=True)
            + ui.kpi(t["real_total"], f"{best.total_sar:,.2f} SAR", "wallet")
            + third
            + ui.kpi(t["quotes_read"], str(len(rows)), "files", sub=t["warned"].format(n=n_warn) if n_warn else "")
            + "</div>", unsafe_allow_html=True)

        # ---- chart card ----
        with st.container(border=True):
            st.markdown(ui.card_head(t["chart"], "chart"), unsafe_allow_html=True)
            chart = pd.DataFrame({
                "supplier": [r.supplier_name for r in rows],
                "SAR": [r.total_sar for r in rows],
                "status": [t["winner"] if r is best else t["incomplete"] if is_inc(r) else t["other"] for r in rows],
            })
            color = alt.Color("status:N", legend=alt.Legend(title=None, orient="bottom"),
                              scale=alt.Scale(domain=[t["winner"], t["other"], t["incomplete"]],
                                              range=[ui.ACCENT, "#8c9aa8", "#dc3545"]))
            y = alt.Y("supplier:N", sort=[r.supplier_name for r in rows], title=None, axis=alt.Axis(labelLimit=260))
            bars = alt.Chart(chart).mark_bar(cornerRadiusEnd=4, height=22).encode(
                x=alt.X("SAR:Q", title="SAR"), y=y, color=color, tooltip=["supplier", "SAR", "status"])
            labels = alt.Chart(chart).mark_text(align="right", dx=-8, fontWeight="bold", color="white").encode(
                x="SAR:Q", y=y, text=alt.Text("SAR:Q", format=",.0f"))
            st.altair_chart((bars + labels).properties(height=60 + 46 * len(rows)), width="stretch")

        # ---- comparison table card ----
        def fmt(v, unit):
            return f"{v} {unit}" if v is not None else "—"

        cols = t["cols"]
        trs = []
        for r in rows:
            cls = "win" if r is best else "inc" if is_inc(r) else ""
            badge = (f'<span class="qa-badge win">{ui.esc(t["winner"])}</span>' if r is best else
                     f'<span class="qa-badge inc">{ui.esc(t["incomplete"])}</span>' if is_inc(r) else "")
            warns = "".join(f'<div class="qa-warn">{ui.esc(ui.warn_text(w, lang))}</div>'
                            for w in r.warnings if not w.startswith("INCOMPLETE"))
            trs.append(f'''<tr class="{cls}">
<td class="qa-num">{r.rank}</td>
<td><b>{ui.esc(r.supplier_name)}</b>{badge}<div class="qa-small"><bdi>{ui.esc(r.source_file)}</bdi> · {r.currency}</div>{warns}</td>
<td class="qa-num"><b>{r.total_sar:,.2f}</b><div class="qa-small">{ui.esc(t["incl"].format(s=f"{r.shipping_fees_sar:,.0f}", v=f"{r.vat_sar:,.0f}"))}</div></td>
<td class="qa-num">{fmt(r.delivery_days, t["days"])}</td>
<td class="qa-num">{fmt(r.credit_days, t["days"])}</td>
<td class="qa-num">{fmt(r.warranty_months, t["months"])}</td>
<td class="qa-num">{fmt(r.validity_days, t["days"])}</td>
<td class="qa-num">{r.total_score:.0f}<div class="qa-bar"><div style="width:{min(r.total_score, 100):.0f}%"></div></div></td>
</tr>''')
        table = ('<div style="overflow-x:auto"><table class="qa-table"><thead><tr>'
                 + "".join(f"<th>{ui.esc(c)}</th>" for c in cols) + "</tr></thead><tbody>"
                 + "".join(trs) + "</tbody></table></div>")
        with st.container(border=True):
            st.markdown(ui.card_head(t["table"], "table") + table, unsafe_allow_html=True)
            st.download_button(t["excel"], to_excel(rows, rlang), "quote_comparison.xlsx",
                               icon=":material/download:")

    rec = res.get("recommendation")
    if rec:
        st.markdown(ui.card(t["why"], "bulb", f"<div style='line-height:1.7'>{ui.esc(rec.summary)}</div>"),
                    unsafe_allow_html=True)
        st.write("")
        c1, c2, c3 = st.columns(3)
        c1.markdown(ui.card(t["reasons"], "check", ui.bullet_list(rec.reasons, "check", ui.ACCENT)),
                    unsafe_allow_html=True)
        c2.markdown(ui.card(t["risks"], "alert", ui.bullet_list(rec.risks, "alert", "#d9822b")),
                    unsafe_allow_html=True)
        c3.markdown(ui.card(t["nego"], "tag", ui.bullet_list(rec.negotiation_points, "tag", "#3d7bd9")),
                    unsafe_allow_html=True)
        st.write("")
        with st.container(border=True):
            st.markdown(ui.card_head(t["email"], "mail"), unsafe_allow_html=True)
            st.text_input(t["subject"], rec.email_subject)
            st.text_area(t["body"], rec.email_body, height=260)
