"""Deterministic math: convert every quote to SAR incl. VAT, then score and rank.

Kept out of the LLM on purpose: money calculations must be exact and auditable.
"""
from __future__ import annotations

from .schemas import Quote, QuoteRow

DEFAULT_VAT = 0.15  # Saudi VAT

# Units of SAR per 1 unit of currency. SAR is pegged to USD at 3.75.
# Edit or override from the UI for other currencies.
DEFAULT_FX = {"SAR": 1.0, "USD": 3.75, "EUR": 4.05, "AED": 1.021, "GBP": 4.75, "CNY": 0.52}

DEFAULT_WEIGHTS = {"price": 50, "delivery": 20, "payment": 15, "warranty": 15}


def check_totals(quote: Quote) -> list[str]:
    """Sanity checks in the quote's own currency. Used by the agent to re-read a document
    when its own extraction does not add up."""
    issues = []
    items_sum = sum((i.total if i.total is not None else i.quantity * i.unit_price) for i in quote.items)
    for i in quote.items:
        if i.total is not None and abs(i.quantity * i.unit_price - i.total) > max(0.01 * i.total, 0.5):
            issues.append(f"Item '{i.description}': quantity x unit_price = {i.quantity * i.unit_price:,.2f} "
                          f"but line total is {i.total:,.2f}")
    if quote.subtotal is not None and items_sum and abs(items_sum - quote.subtotal) > 0.01 * quote.subtotal:
        issues.append(f"Items add up to {items_sum:,.2f} but subtotal is {quote.subtotal:,.2f}")
    if quote.total_amount:
        base = quote.subtotal if quote.subtotal is not None else items_sum
        extras = (quote.shipping_cost or 0) + (quote.other_fees or 0)
        vat_rate = quote.vat_rate if quote.vat_rate is not None else DEFAULT_VAT
        candidates = [base + extras] if quote.prices_include_vat else [base + extras, (base + extras) * (1 + vat_rate)]
        if all(abs(c - quote.total_amount) > 0.01 * quote.total_amount for c in candidates):
            issues.append(
                f"Stated grand total is {quote.total_amount:,.2f} but items {base:,.2f} + shipping/fees "
                f"{extras:,.2f} (+VAT if excluded) do not reach it. Check shipping_cost, other_fees and VAT."
            )
    return issues


def normalize(quote: Quote, source_file: str, fx: dict[str, float] | None = None) -> QuoteRow:
    fx = fx or DEFAULT_FX
    warnings: list[str] = []

    cur = (quote.currency or "SAR").upper().strip()
    rate = fx.get(cur)
    if rate is None:
        warnings.append(f"Unknown currency {cur}; treated as SAR")
        rate = 1.0

    items_sum = sum((i.total if i.total is not None else i.quantity * i.unit_price) for i in quote.items)
    base = quote.subtotal if quote.subtotal is not None else items_sum
    warnings += [f"CHECK NUMBERS: {x}" for x in check_totals(quote)]

    extras = (quote.shipping_cost or 0) + (quote.other_fees or 0)
    vat_rate = quote.vat_rate if quote.vat_rate is not None else DEFAULT_VAT

    if quote.prices_include_vat:
        gross = base + extras
        vat = gross - gross / (1 + vat_rate)
        base, extras = base / (1 + vat_rate), extras / (1 + vat_rate)  # show net figures
    else:
        vat = (base + extras) * vat_rate
        gross = base + extras + vat

    for field, label in [
        (quote.delivery_days, "delivery time"),
        (quote.credit_days, "payment terms"),
        (quote.warranty_months, "warranty"),
        (quote.validity_days, "offer validity"),
    ]:
        if field is None:
            warnings.append(f"Missing {label}")

    return QuoteRow(
        supplier_name=quote.supplier_name,
        source_file=source_file,
        currency=cur,
        subtotal_sar=round(base * rate, 2),
        shipping_fees_sar=round(extras * rate, 2),
        vat_sar=round(vat * rate, 2),
        total_sar=round(gross * rate, 2),
        delivery_days=quote.delivery_days,
        credit_days=quote.credit_days,
        warranty_months=quote.warranty_months,
        validity_days=quote.validity_days,
        payment_terms=quote.payment_terms,
        item_count=len(quote.items),
        score_price=0,
        score_delivery=0,
        score_payment=0,
        score_warranty=0,
        total_score=0,
        warnings=warnings,
        conditions=quote.conditions,
    )


def _lower_is_better(values: list[float | None]) -> list[float]:
    known = [v for v in values if v is not None and v > 0]
    if not known:
        return [0.0 for _ in values]
    best = min(known)
    return [round(best / v * 100, 1) if v else 0.0 for v in values]


def _higher_is_better(values: list[float | None]) -> list[float]:
    known = [v for v in values if v is not None]
    best = max(known) if known else 0
    if best <= 0:  # nobody offers it -> neutral for those who stated it
        return [100.0 if v is not None else 0.0 for v in values]
    return [round(v / best * 100, 1) if v is not None else 0.0 for v in values]


def score(rows: list[QuoteRow], weights: dict[str, float] | None = None) -> list[QuoteRow]:
    weights = weights or DEFAULT_WEIGHTS
    total_w = sum(weights.values()) or 1

    price = _lower_is_better([r.total_sar for r in rows])
    delivery = _lower_is_better([r.delivery_days for r in rows])
    payment = _higher_is_better([r.credit_days for r in rows])
    warranty = _higher_is_better([r.warranty_months for r in rows])

    max_items = max((r.item_count for r in rows), default=0)
    for r, p, d, pay, w in zip(rows, price, delivery, payment, warranty):
        r.score_price, r.score_delivery, r.score_payment, r.score_warranty = p, d, pay, w
        r.total_score = round(
            (p * weights.get("price", 0) + d * weights.get("delivery", 0)
             + pay * weights.get("payment", 0) + w * weights.get("warranty", 0)) / total_w,
            1,
        )
        if r.item_count < max_items:
            r.warnings.append(
                f"INCOMPLETE: quotes {r.item_count} of {max_items} items - its total is not comparable, ranked last"
            )

    # A quote that leaves items out looks cheaper than it is, so complete quotes always rank first.
    ranked = sorted(rows, key=lambda r: (r.item_count == max_items, r.total_score), reverse=True)
    for i, r in enumerate(ranked, 1):
        r.rank = i
    return ranked
