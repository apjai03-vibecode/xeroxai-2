"""Data models and schemas for the XeroxAI 2.0 application.

Defines Pydantic request and response schemas, enumerations, and validation models
for SmartDoc vision corrections, photo presets, billing calculations, orders, and biodata.
"""

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class PhotoPreset(str, Enum):
    """Supported government and standard ID photo specifications."""

    TNPSC_UPSC = "tnpsc_upsc"
    PASSPORT_STANDARD = "passport_standard"
    SIGNATURE = "signature"


class BiodataRequest(BaseModel):
    """Request payload containing raw customer notes for biodata generation."""

    raw_text: str = Field(
        ...,
        description="Unstructured customer notes, biodata paste, or rough WhatsApp message.",
    )


class BiodataSchema(BaseModel):
    """Structured candidate information extracted from raw customer notes."""

    full_name: str = Field(default="", description="Full Name of candidate.")
    dob: str = Field(
        default="", description="Date of birth in DD/MM/YYYY or YYYY-MM-DD format."
    )
    qualification: str = Field(
        default="", description="Highest educational degree, diploma, or certificate."
    )
    contact: str = Field(default="", description="Primary telephone or mobile number.")
    email: str = Field(default="", description="Candidate email address.")
    address: str = Field(
        default="", description="Residential or communication postal address."
    )
    skills: list[str] = Field(
        default_factory=list, description="Key professional and technical skills."
    )
    languages: list[str] = Field(
        default_factory=list, description="Spoken and written languages."
    )


class BiodataResponse(BaseModel):
    """Response payload returning extracted biodata and optional base64 PDF."""

    extracted_data: BiodataSchema
    is_fallback: bool
    model_used: str
    pdf_base64: Optional[str] = None
    processing_time_ms: float


class QueueEstimateRequest(BaseModel):
    """Request parameters for turnaround time prediction and counter rate pricing."""

    page_count: int = Field(ge=1, le=1000, description="Total number of pages to print.")
    is_color: bool = Field(
        default=False, description="Whether full-color printing is required."
    )
    needs_lamination: bool = Field(
        default=False, description="Whether thermal lamination finishing is needed."
    )
    current_queue_customers: int = Field(
        default=0,
        ge=0,
        le=50,
        description="Number of customers waiting ahead in queue.",
    )


class QueuePriceBreakdown(BaseModel):
    """Detailed fee breakdown for an estimated print shop job."""

    printing_fee: float
    lamination_fee: float
    rush_buffer: float
    total_fee: float
    currency: str = "INR"


class QueueEstimateResponse(BaseModel):
    """Response payload containing estimated wait time and suggested counter pricing."""

    estimated_wait_minutes: float
    price_breakdown: QueuePriceBreakdown
    model_info: dict[str, Any]
    processing_time_ms: float


class SmartDocResponse(BaseModel):
    """Diagnostic and visual output from the SmartDoc AI vision correction pipeline."""

    filename: str
    is_pdf: bool
    width: int
    height: int
    blur_score: float
    is_blurry: bool
    detected_skew_deg: float
    perspective_corrected: bool
    shadows_removed: bool
    output_mode: str
    reliability_notes: list[str]
    original_preview_base64: str
    processed_preview_base64: str
    processing_time_ms: float


class PricingConfigModel(BaseModel):
    """Configurable print shop rate card stored persistently in SQLite."""

    bw_single: float = 2.0
    bw_double: float = 3.0
    color_single: float = 10.0
    color_double: float = 16.0
    a3_multiplier: float = 2.0
    legal_multiplier: float = 1.25
    letter_multiplier: float = 1.0
    lamination_a4: float = 20.0
    lamination_a3: float = 40.0
    updated_at: Optional[str] = None


class OrderItemModel(BaseModel):
    """Individual print job line item specification."""

    page_count: int = Field(default=1, ge=1)
    is_color: bool = Field(default=False)
    is_double_sided: bool = Field(default=False)
    paper_size: str = Field(default="A4")
    copies: int = Field(default=1, ge=1)
    needs_lamination: bool = Field(default=False)
    description: Optional[str] = ""
    unit_rate: Optional[float] = 0.0
    print_cost: Optional[float] = 0.0
    lamination_cost: Optional[float] = 0.0
    subtotal: Optional[float] = 0.0


class BillingCalculationRequest(BaseModel):
    """Request payload containing line items for deterministic billing calculation."""

    items: list[OrderItemModel]


class BillingCalculationResponse(BaseModel):
    """Itemized billing calculation response calculated with persistent shop rates."""

    items: list[dict[str, Any]]
    total_sheets: int
    grand_total: float
    currency: str = "INR"


class OrderCreateRequest(BaseModel):
    """Customer and item specifications to create a new persistent counter order."""

    customer_name: str = Field(..., min_length=1)
    customer_phone: Optional[str] = ""
    items: list[OrderItemModel]
    notes: Optional[str] = ""
    status: Optional[str] = "Pending"


class OrderStatusUpdateRequest(BaseModel):
    """Request payload to transition order lifecycle status."""

    status: str = Field(..., description="Pending, Processing, or Completed")


class OrderResponse(BaseModel):
    """Full order record retrieved from persistent SQLite storage."""

    id: int
    order_id: str
    customer_name: str
    customer_phone: str
    items: list[dict[str, Any]]
    total_amount: float
    status: str
    notes: str
    created_at: str
    updated_at: str


class OrderParseRequest(BaseModel):
    """Natural-language counter request entered by the operator."""

    natural_text: str = Field(..., min_length=3)


class OrderParseResponse(BaseModel):
    """Structured order parameters extracted from natural language counter input."""

    parsed_order: dict[str, Any]
    is_fallback: bool
    model_used: str
    calculated_billing: BillingCalculationResponse
