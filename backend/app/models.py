from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class PhotoPreset(str, Enum):
    TNPSC_UPSC = "tnpsc_upsc"
    PASSPORT_STANDARD = "passport_standard"
    SIGNATURE = "signature"

class BiodataRequest(BaseModel):
    raw_text: str = Field(..., description="Unstructured customer notes, biodata paste, or rough WhatsApp message")

class BiodataSchema(BaseModel):
    full_name: str = Field(default="", description="Full Name of candidate")
    dob: str = Field(default="", description="Date of birth in DD/MM/YYYY or YYYY-MM-DD")
    qualification: str = Field(default="", description="Highest educational degree/diploma")
    contact: str = Field(default="", description="Phone number")
    email: str = Field(default="", description="Email address")
    address: str = Field(default="", description="Residential / communication address")
    skills: list[str] = Field(default_factory=list, description="Key skills and proficiencies")
    languages: list[str] = Field(default_factory=list, description="Known languages")

class BiodataResponse(BaseModel):
    extracted_data: BiodataSchema
    is_fallback: bool
    model_used: str
    pdf_base64: Optional[str] = None
    processing_time_ms: float

class QueueEstimateRequest(BaseModel):
    page_count: int = Field(ge=1, le=1000, description="Total number of pages to print")
    is_color: bool = Field(default=False, description="Whether color printing is required")
    needs_lamination: bool = Field(default=False, description="Whether lamination finishing is needed")
    current_queue_customers: int = Field(default=0, ge=0, le=50, description="Number of customers waiting ahead in queue")

class QueuePriceBreakdown(BaseModel):
    printing_fee: float
    lamination_fee: float
    rush_buffer: float
    total_fee: float
    currency: str = "INR"

class QueueEstimateResponse(BaseModel):
    estimated_wait_minutes: float
    price_breakdown: QueuePriceBreakdown
    model_info: dict[str, Any]
    processing_time_ms: float

# ============================================================
# XeroxAI 2.0 Models: SmartDoc, Billing, Orders, AI Assistant
# ============================================================

class SmartDocResponse(BaseModel):
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
    reliability_notes: List[str]
    original_preview_base64: str
    processed_preview_base64: str
    processing_time_ms: float

class PricingConfigModel(BaseModel):
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
    items: List[OrderItemModel]

class BillingCalculationResponse(BaseModel):
    items: List[Dict[str, Any]]
    total_sheets: int
    grand_total: float
    currency: str = "INR"

class OrderCreateRequest(BaseModel):
    customer_name: str = Field(..., min_length=1)
    customer_phone: Optional[str] = ""
    items: List[OrderItemModel]
    notes: Optional[str] = ""
    status: Optional[str] = "Pending"

class OrderStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="Pending, Processing, or Completed")

class OrderResponse(BaseModel):
    id: int
    order_id: str
    customer_name: str
    customer_phone: str
    items: List[Dict[str, Any]]
    total_amount: float
    status: str
    notes: str
    created_at: str
    updated_at: str

class OrderParseRequest(BaseModel):
    natural_text: str = Field(..., min_length=3)

class OrderParseResponse(BaseModel):
    parsed_order: Dict[str, Any]
    is_fallback: bool
    model_used: str
    calculated_billing: BillingCalculationResponse
