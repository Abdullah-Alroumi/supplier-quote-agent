"""Data models shared by every step of the agent."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class LineItem(BaseModel):
    description: str = Field(description="Item or service name as written in the quote")
    quantity: float = Field(description="Quantity offered")
    unit: Optional[str] = Field(default=None, description="Unit of measure, e.g. ton, piece, box")
    unit_price: float = Field(description="Price per unit in the quote currency")
    total: Optional[float] = Field(default=None, description="Line total in the quote currency, if stated")


class Quote(BaseModel):
    """Everything we need from one supplier quotation, extracted by the LLM."""

    supplier_name: str = Field(description="Name of the supplier company")
    quote_reference: Optional[str] = Field(default=None, description="Quote / proposal number")
    currency: str = Field(description="ISO currency code of the prices, e.g. SAR, USD, EUR")
    items: list[LineItem] = Field(default_factory=list)
    subtotal: Optional[float] = Field(default=None, description="Sum of items before VAT, shipping and fees")
    prices_include_vat: bool = Field(
        default=False,
        description="True only if the quote explicitly says prices already include VAT",
    )
    vat_rate: Optional[float] = Field(default=None, description="VAT rate as a fraction, e.g. 0.15")
    shipping_cost: float = Field(default=0.0, description="Delivery / freight cost. 0 if free or included")
    other_fees: float = Field(default=0.0, description="Any other extra charges (customs, handling, ...)")
    total_amount: Optional[float] = Field(default=None, description="Grand total as stated in the quote")
    delivery_days: Optional[int] = Field(default=None, description="Delivery lead time in days (convert weeks to days)")
    payment_terms: Optional[str] = Field(default=None, description="Payment terms as written")
    credit_days: Optional[int] = Field(
        default=None,
        description="Days of credit given to the buyer. 0 for advance payment / cash on order",
    )
    warranty_months: Optional[int] = Field(default=None, description="Warranty or quality guarantee in months")
    validity_days: Optional[int] = Field(default=None, description="How many days the offer is valid")
    conditions: list[str] = Field(
        default_factory=list,
        description="Important conditions, exclusions or risks (e.g. 'price subject to change', 'excludes unloading')",
    )


class QuoteRow(BaseModel):
    """One row of the final comparison table (all money in SAR)."""

    supplier_name: str
    source_file: str
    currency: str
    subtotal_sar: float
    shipping_fees_sar: float
    vat_sar: float
    total_sar: float
    delivery_days: Optional[int]
    credit_days: Optional[int]
    warranty_months: Optional[int]
    validity_days: Optional[int]
    payment_terms: Optional[str]
    item_count: int
    score_price: float
    score_delivery: float
    score_payment: float
    score_warranty: float
    total_score: float
    rank: int = 0
    warnings: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    best_supplier: str = Field(description="Exact supplier name of the recommended option")
    summary: str = Field(description="Two or three sentence executive summary of the decision")
    reasons: list[str] = Field(description="Why this supplier wins, concrete and number-based")
    risks: list[str] = Field(description="Risks or missing information the buyer should check")
    negotiation_points: list[str] = Field(description="Specific points to negotiate with the chosen supplier")
    email_subject: str = Field(description="Subject of a reply email to the chosen supplier")
    email_body: str = Field(description="Polite, ready-to-send email to the chosen supplier")
