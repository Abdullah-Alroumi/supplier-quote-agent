"""LangGraph workflow:

    START -> extract (one parallel branch per file) -> compare -> recommend -> END
"""
from __future__ import annotations

import json
import operator
from typing import Annotated, Any, Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from .llm import get_model
from .loaders import LoadedDoc
from .schemas import Quote, QuoteRow, Recommendation
from .scoring import DEFAULT_FX, DEFAULT_WEIGHTS, check_totals, normalize, score


class AgentState(TypedDict, total=False):
    docs: list[LoadedDoc]
    language: str  # "ar" or "en"
    weights: dict[str, float]
    fx: dict[str, float]
    model: Optional[str]
    quotes: Annotated[list[dict[str, Any]], operator.add]
    errors: Annotated[list[str], operator.add]
    rows: list[QuoteRow]
    recommendation: Recommendation


EXTRACT_SYSTEM = """You extract supplier quotations for a procurement team in Saudi Arabia.
The document may be in Arabic, English or both, and may be a PDF, a scan or an email.
Rules:
- Copy numbers exactly as written. Never invent values: leave a field empty if it is not stated.
- Convert delivery weeks to days. "Immediate" or "ex-stock" = 1 day.
- credit_days: 0 for advance payment or cash on order; 30 for "net 30"; 60 for "60 days from invoice".
- prices_include_vat is true ONLY when the quote clearly says prices include VAT (شامل الضريبة).
- shipping_cost is 0 when delivery is free or included (التوصيل مجاني / شامل التوصيل).
- shipping_cost and other_fees come ONLY from lines explicitly labelled shipping, delivery, freight,
  transport, customs or fees (شحن، نقل، توصيل، رسوم). Never put an item's line total there.
- Every product line goes in items, with its own quantity, unit_price and line total.
- total_amount is the grand total exactly as printed (before or after VAT, whichever the quote shows).
- List conditions that could cost the buyer money or time (exclusions, price escalation, short validity)."""


def _doc_message(doc: LoadedDoc) -> HumanMessage:
    parts: list[dict] = [{"type": "text", "text": f"File name: {doc.name}\n\n{doc.text or '(see images)'}"}]
    for img in doc.images:
        parts.append({"type": "image", "base64": img, "mime_type": doc.mime})
    return HumanMessage(content=parts)


# ---------- nodes ----------

def fan_out(state: AgentState):
    return [Send("extract", {"doc": d, "model": state.get("model")}) for d in state["docs"]]


MAX_REVIEWS = 1  # extra self-correction passes when the numbers do not add up


def extract(payload: dict) -> dict:
    """Extract one quote, then self-check: if the extracted numbers do not reconcile with the
    stated totals, show the agent its own mistakes and let it re-read the document."""
    doc: LoadedDoc = payload["doc"]
    try:
        llm = get_model(payload.get("model")).with_structured_output(Quote)
        messages = [SystemMessage(EXTRACT_SYSTEM), _doc_message(doc)]
        quote = llm.invoke(messages)
        for _ in range(MAX_REVIEWS):
            issues = check_totals(quote)
            if not issues:
                break
            review = HumanMessage(
                "Your extraction below does not add up:\n- " + "\n- ".join(issues)
                + "\n\nYour previous answer:\n" + quote.model_dump_json(indent=1)
                + "\n\nRe-read the document carefully and return the corrected extraction."
            )
            quote = llm.invoke(messages + [review])
        return {"quotes": [{"source_file": doc.name, "quote": quote}]}
    except Exception as e:  # one bad file must not kill the whole comparison
        return {"errors": [f"{doc.name}: {e}"]}


def compare(state: AgentState) -> dict:
    fx = {**DEFAULT_FX, **(state.get("fx") or {})}
    rows = [normalize(q["quote"], q["source_file"], fx) for q in state.get("quotes", [])]
    return {"rows": score(rows, state.get("weights") or DEFAULT_WEIGHTS)}


def recommend(state: AgentState) -> dict:
    rows = state.get("rows") or []
    if not rows:
        return {}
    lang = "Arabic (clear Modern Standard Arabic)" if state.get("language", "ar") == "ar" else "English"
    table = [r.model_dump() for r in rows]
    system = f"""You are a senior procurement analyst. Write everything in {lang}.
You receive a comparison table that was ALREADY calculated by code (all amounts in SAR including VAT).
Trust these numbers; do not recalculate them. Recommend the rank-1 supplier unless a warning makes it risky. Never recommend a quote marked INCOMPLETE.
and if you deviate, say exactly why. Be concrete: quote SAR differences and days.
The email goes to the chosen supplier: confirm interest, ask to confirm any missing details,
and include one or two negotiation requests. Sign it as "[Your name] - Procurement"."""
    llm = get_model(state.get("model")).with_structured_output(Recommendation)
    rec = llm.invoke([SystemMessage(system), HumanMessage(json.dumps(table, ensure_ascii=False, indent=1))])
    return {"recommendation": rec}


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("extract", extract)
    g.add_node("compare", compare)
    g.add_node("recommend", recommend)
    g.add_conditional_edges(START, fan_out, ["extract"])
    g.add_edge("extract", "compare")
    g.add_edge("compare", "recommend")
    g.add_edge("recommend", END)
    return g.compile()


def run(docs: list[LoadedDoc], language: str = "ar", weights: dict | None = None,
        fx: dict | None = None, model: str | None = None) -> AgentState:
    return build_graph().invoke(
        {"docs": docs, "language": language, "weights": weights or DEFAULT_WEIGHTS,
         "fx": fx or {}, "model": model, "quotes": [], "errors": []}
    )
