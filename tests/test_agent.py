"""Offline tests: math, file loading and the full graph with a fake LLM (no API key needed)."""
from pathlib import Path

import pytest

from quote_agent import graph as graph_mod
from quote_agent.loaders import load_path
from quote_agent.schemas import LineItem, Quote, Recommendation
from quote_agent.scoring import normalize, score

SAMPLES = Path(__file__).resolve().parent.parent / "samples"

QA = Quote(supplier_name="Gulf Polymers", currency="SAR", subtotal=97000,
           items=[LineItem(description="HDPE", quantity=20, unit="ton", unit_price=4850)],
           delivery_days=7, credit_days=30, warranty_months=6, validity_days=15)
QB = Quote(supplier_name="Asia Plastics", currency="USD", shipping_cost=1900,
           items=[LineItem(description="HDPE", quantity=20, unit="MT", unit_price=1240)],
           delivery_days=35, credit_days=0, warranty_months=0, validity_days=10)
QC = Quote(supplier_name="Al-Sharq Supply", currency="SAR", prices_include_vat=True,
           items=[LineItem(description="HDPE", quantity=20, unit="ton", unit_price=5300)],
           delivery_days=10, credit_days=60, warranty_months=12, validity_days=30)


def test_normalization_to_sar_incl_vat():
    assert normalize(QA, "a").total_sar == 111550.00
    assert normalize(QB, "b").total_sar == 115143.75
    assert normalize(QC, "c").total_sar == 106000.00
    c = normalize(QC, "c")
    assert c.vat_sar == pytest.approx(13826.09, abs=0.01)
    assert c.subtotal_sar + c.shipping_fees_sar + c.vat_sar == pytest.approx(106000, abs=0.02)


def test_highest_headline_price_wins_after_normalization():
    ranked = score([normalize(QA, "a"), normalize(QB, "b"), normalize(QC, "c")])
    assert ranked[0].supplier_name == "Al-Sharq Supply"
    assert ranked[0].score_price == 100
    assert [r.rank for r in ranked] == [1, 2, 3]


def test_incomplete_quote_cannot_win_on_price():
    cheap_but_partial = QB.model_copy(update={"supplier_name": "Partial", "currency": "SAR", "shipping_cost": 0,
                                              "items": [LineItem(description="x", quantity=1, unit_price=10)]})
    full = QA.model_copy(update={"items": QA.items * 2})
    ranked = score([normalize(cheap_but_partial, "p"), normalize(full, "f")])
    assert ranked[0].supplier_name == "Gulf Polymers"
    assert any("INCOMPLETE" in w for w in ranked[1].warnings)


def test_missing_fields_are_flagged():
    q = Quote(supplier_name="X", currency="SAR", items=[LineItem(description="a", quantity=1, unit_price=10)])
    row = normalize(q, "x")
    assert any("delivery" in w for w in row.warnings)


@pytest.mark.skipif(not SAMPLES.exists(), reason="run scripts/make_samples.py first")
def test_loaders_read_samples():
    a = load_path(SAMPLES / "quote_A_gulf_polymers.pdf")
    c = load_path(SAMPLES / "quote_C_alsharq_email.eml")
    assert "4,850.00" in a.text and not a.images
    assert "5,300" in c.text and "شامل" in c.text


class _FakeStructured:
    def __init__(self, schema):
        self.schema = schema

    def invoke(self, messages):
        if self.schema is Recommendation:
            return Recommendation(best_supplier="Al-Sharq Supply", summary="s", reasons=["r"],
                                  risks=[], negotiation_points=[], email_subject="x", email_body="y")
        text = messages[-1].content[0]["text"]
        return QA if "quote_A" in text else QB if "quote_B" in text else QC


class _FakeModel:
    def with_structured_output(self, schema):
        return _FakeStructured(schema)


@pytest.mark.skipif(not SAMPLES.exists(), reason="run scripts/make_samples.py first")
def test_full_graph_with_fake_llm(monkeypatch):
    monkeypatch.setattr(graph_mod, "get_model", lambda model=None: _FakeModel())
    docs = [load_path(p) for p in sorted(SAMPLES.iterdir())]
    out = graph_mod.run(docs, language="en")
    assert not out["errors"]
    assert len(out["rows"]) == 3
    assert out["rows"][0].supplier_name == "Al-Sharq Supply"
    assert out["recommendation"].best_supplier == "Al-Sharq Supply"


WRONG_WAFA = Quote(supplier_name="Al-Wafa", currency="SAR", prices_include_vat=True, shipping_cost=17500,
                   total_amount=40300,
                   items=[LineItem(description="carton", quantity=5000, unit_price=3.5, total=17500),
                          LineItem(description="film", quantity=200, unit_price=42, total=8400),
                          LineItem(description="pallet", quantity=300, unit_price=48, total=14400)])


def test_check_totals_catches_line_total_read_as_shipping():
    from quote_agent.scoring import check_totals
    assert check_totals(WRONG_WAFA)
    assert not check_totals(WRONG_WAFA.model_copy(update={"shipping_cost": 0}))
    # A pre-VAT stated total (like Asia Plastics' 'TOTAL USD 26,700') is not an error
    assert not check_totals(QB.model_copy(update={"total_amount": 26700}))


def test_agent_self_corrects_when_numbers_do_not_add_up(monkeypatch):
    calls = []

    class Model:
        def with_structured_output(self, schema):
            class S:
                def invoke(self, messages):
                    calls.append(messages)
                    return WRONG_WAFA if len(calls) == 1 else WRONG_WAFA.model_copy(update={"shipping_cost": 0})
            return S()

    monkeypatch.setattr(graph_mod, "get_model", lambda model=None: Model())
    from quote_agent.loaders import LoadedDoc
    out = graph_mod.extract({"doc": LoadedDoc(name="wafa.png", text="x")})
    assert len(calls) == 2 and "does not add up" in calls[1][-1].content
    assert out["quotes"][0]["quote"].shipping_cost == 0
    assert normalize(out["quotes"][0]["quote"], "w").total_sar == 40300
