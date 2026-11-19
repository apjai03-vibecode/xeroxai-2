"""FastAPI REST API router and application entrypoint for XeroxAI 2.0.

Exposes REST endpoints for SmartDoc AI vision enhancement, government photo cropping,
ReportLab biodata generation, TabPFN queue estimation, smart billing, and order management.
"""

import base64
import logging
import time
from typing import Any, Optional
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.biodata_engine import extract_biodata_with_gemma, generate_biodata_pdf
from app.config import settings
from app.database import (
    create_order,
    get_order_by_id,
    get_pricing_config,
    init_db,
    list_orders,
    update_order_status,
    update_pricing_config,
)
from app.estimator import estimator_engine
from app.models import (
    BillingCalculationRequest,
    BillingCalculationResponse,
    BiodataRequest,
    BiodataResponse,
    BiodataSchema,
    OrderCreateRequest,
    OrderParseRequest,
    OrderParseResponse,
    OrderResponse,
    OrderStatusUpdateRequest,
    PhotoPreset,
    PricingConfigModel,
    QueueEstimateRequest,
    QueueEstimateResponse,
    SmartDocResponse,
)
from app.order_engine import (
    calculate_order_total,
    parse_order_with_ai,
)
from app.photo_engine import process_photo
from app.smartdoc_engine import process_document
from app.telemetry import get_recent_telemetry, init_telemetry, trace_span

logger = logging.getLogger(__name__)

# Initialize Sentry distributed tracing and SQLite DB
init_telemetry()
init_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",
    description="XeroxAI 2.0 – Intelligent Print Shop & Document Automation System",
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-Dimensions",
        "X-File-Size-KB",
        "X-Preset-Applied",
        "X-Blur-Score",
        "X-Skew-Angle",
        "Content-Disposition",
    ],
)


@app.get("/")
def health_check() -> dict[str, Any]:
    """Returns application health status, version, and active service integrations.

    Returns:
        Dictionary detailing API status and model configuration state.
    """
    return {
        "status": "online",
        "service": "XeroxAI 2.0 Backend",
        "version": "2.0.0",
        "features": [
            "smartdoc_ai",
            "photo_spec_engine",
            "smart_billing",
            "ai_order_assistant",
            "order_management",
            "biodata_generator",
            "queue_estimator",
        ],
        "sponsor_integrations": {
            "gemma": {
                "model": settings.GEMMA_MODEL,
                "endpoint": settings.OLLAMA_BASE_URL,
            },
            "tabpfn": {
                "engine": estimator_engine.engine_name,
                "is_native": estimator_engine.is_tabpfn_loaded,
            },
            "sentry": {
                "tracing_enabled": True,
                "environment": settings.ENVIRONMENT,
            },
        },
    }


# -------------------------------------------------------------
# 1. SmartDoc AI Engine (OpenCV + PIL)
# -------------------------------------------------------------
@app.post("/api/smartdoc/enhance/", response_model=SmartDocResponse)
async def enhance_document(
    file: UploadFile = File(..., description="Uploaded document (JPG, PNG, PDF)"),
    output_mode: str = Form(
        "enhanced_color", description="'enhanced_color' or 'clean_bw'"
    ),
    auto_deskew: bool = Form(True),
    auto_perspective: bool = Form(True),
    remove_shadows: bool = Form(True),
) -> SmartDocResponse:
    """Enhances uploaded document via OpenCV vision corrections without text alteration.

    Args:
        file: Uploaded image (JPG, PNG, WebP) or PDF file.
        output_mode: Color mode ('enhanced_color' or 'clean_bw').
        auto_deskew: Whether to correct paper tilt.
        auto_perspective: Whether to detect boundaries and warp perspective.
        remove_shadows: Whether to normalize uneven counter lighting.

    Returns:
        SmartDocResponse with base64 previews, clarity metrics, and diagnostic notes.

    Raises:
        HTTPException: If file is empty or processing fails.
    """
    start_time = time.perf_counter()
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded document is empty.")

    try:
        with trace_span(
            op="smartdoc.enhancement",
            description=f"SmartDoc document cleanup for {file.filename}",
            tags={"output_mode": output_mode, "filename": file.filename or "doc"},
            data={"file_size": len(contents)},
        ):
            doc_result = process_document(
                input_bytes=contents,
                filename=file.filename or "document.jpg",
                output_mode=output_mode,
                auto_deskew=auto_deskew,
                auto_perspective=auto_perspective,
                remove_shadows=remove_shadows,
            )

        orig_b64 = base64.b64encode(doc_result["original_bytes"]).decode("utf-8")
        proc_b64 = base64.b64encode(doc_result["processed_bytes"]).decode("utf-8")
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return SmartDocResponse(
            filename=doc_result["filename"],
            is_pdf=doc_result["is_pdf"],
            width=doc_result["width"],
            height=doc_result["height"],
            blur_score=doc_result["blur_score"],
            is_blurry=doc_result["is_blurry"],
            detected_skew_deg=doc_result["detected_skew_deg"],
            perspective_corrected=doc_result["perspective_corrected"],
            shadows_removed=doc_result["shadows_removed"],
            output_mode=doc_result["output_mode"],
            reliability_notes=doc_result["reliability_notes"],
            original_preview_base64=orig_b64,
            processed_preview_base64=proc_b64,
            processing_time_ms=duration_ms,
        )
    except Exception as exc:
        logger.error("SmartDoc processing error: %s", exc)
        raise HTTPException(
            status_code=500, detail=f"SmartDoc processing error: {str(exc)}"
        )


@app.post("/api/smartdoc/download/")
async def download_enhanced_document(
    file: UploadFile = File(...),
    output_mode: str = Form("enhanced_color"),
    auto_deskew: bool = Form(True),
    auto_perspective: bool = Form(True),
    remove_shadows: bool = Form(True),
) -> Response:
    """Processes document and returns downloadable JPEG binary with diagnostic headers.

    Args:
        file: Uploaded image or PDF file.
        output_mode: Color mode ('enhanced_color' or 'clean_bw').
        auto_deskew: Whether to correct tilt.
        auto_perspective: Whether to warp perspective.
        remove_shadows: Whether to remove shadows.

    Returns:
        FastAPI Response with JPEG binary stream.

    Raises:
        HTTPException: If file is empty.
    """
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="File is empty.")

    doc_result = process_document(
        input_bytes=contents,
        filename=file.filename or "document.jpg",
        output_mode=output_mode,
        auto_deskew=auto_deskew,
        auto_perspective=auto_perspective,
        remove_shadows=remove_shadows,
    )

    out_filename = f"xeroxai_enhanced_{doc_result['filename'].split('.')[0]}.jpg"
    return Response(
        content=doc_result["processed_bytes"],
        media_type="image/jpeg",
        headers={
            "Content-Disposition": f'attachment; filename="{out_filename}"',
            "X-Blur-Score": str(doc_result["blur_score"]),
            "X-Skew-Angle": str(doc_result["detected_skew_deg"]),
        },
    )


# -------------------------------------------------------------
# 2. Photo Spec Engine (Local PIL)
# -------------------------------------------------------------
@app.post("/api/resize-photo/")
async def resize_photo(
    file: UploadFile = File(..., description="Uploaded image file (JPEG/PNG/WEBP)"),
    preset: PhotoPreset = Form(
        PhotoPreset.TNPSC_UPSC, description="Govt/Exam or ID photo preset"
    ),
) -> Response:
    """Crops, resizes, and dynamically compresses photos to exact official preset boundaries.

    Args:
        file: Uploaded candidate photo.
        preset: Target preset specification from PhotoPreset enum.

    Returns:
        FastAPI Response containing binary JPEG with metadata headers.

    Raises:
        HTTPException: If uploaded image is empty or invalid.
    """
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        processed_bytes, headers = process_photo(contents, preset)

        return Response(
            content=processed_bytes, media_type="image/jpeg", headers=headers
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Image processing failed for %s: %s", preset.value, exc)
        raise HTTPException(
            status_code=500, detail=f"Image processing failed: {str(exc)}"
        )


# -------------------------------------------------------------
# 3. Biodata Generator Engine (Gemma + ReportLab)
# -------------------------------------------------------------
@app.post("/api/generate-biodata/", response_model=BiodataResponse)
async def generate_biodata(req: BiodataRequest) -> BiodataResponse:
    """Extracts biographical fields from customer notes and generates a base64 PDF.

    Args:
        req: Validated BiodataRequest containing informal notes text.

    Returns:
        BiodataResponse containing structured schema and base64-encoded PDF.

    Raises:
        HTTPException: If notes are empty or PDF creation fails.
    """
    start_time = time.perf_counter()
    if not req.raw_text.strip():
        raise HTTPException(status_code=400, detail="Raw text notes cannot be empty.")

    schema, is_fallback, model_used = extract_biodata_with_gemma(req.raw_text)

    try:
        pdf_bytes = generate_biodata_pdf(schema)
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    except Exception as exc:
        logger.error("PDF generation failed: %s", exc)
        raise HTTPException(
            status_code=500, detail=f"PDF generation failed: {str(exc)}"
        )

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return BiodataResponse(
        extracted_data=schema,
        is_fallback=is_fallback,
        model_used=model_used,
        pdf_base64=pdf_b64,
        processing_time_ms=duration_ms,
    )


@app.post("/api/download-biodata-pdf/")
async def download_biodata_pdf(schema: BiodataSchema) -> Response:
    """Generates and streams a ready-to-print A4 PDF based on structured biodata schema.

    Args:
        schema: Validated BiodataSchema fields.

    Returns:
        FastAPI Response with application/pdf binary content.

    Raises:
        HTTPException: If PDF compilation fails.
    """
    try:
        pdf_bytes = generate_biodata_pdf(schema)
        filename = (
            f"{schema.full_name.replace(' ', '_')}_Biodata.pdf"
            if schema.full_name
            else "Biodata.pdf"
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        logger.error("PDF generation failed: %s", exc)
        raise HTTPException(
            status_code=500, detail=f"PDF generation failed: {str(exc)}"
        )


# -------------------------------------------------------------
# 4. Queue Estimator
# -------------------------------------------------------------
@app.post("/api/estimate-job/", response_model=QueueEstimateResponse)
async def estimate_job(req: QueueEstimateRequest) -> QueueEstimateResponse:
    """Predicts wait time and fair counter charges for a print queue request.

    Args:
        req: Validated QueueEstimateRequest parameters.

    Returns:
        QueueEstimateResponse with wait-time minutes and fee breakdown.
    """
    start_time = time.perf_counter()

    turnaround_mins, model_info = estimator_engine.predict_turnaround(
        page_count=req.page_count,
        is_color=req.is_color,
        needs_lamination=req.needs_lamination,
        current_queue=req.current_queue_customers,
    )

    pricing = estimator_engine.calculate_pricing(req, turnaround_mins)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return QueueEstimateResponse(
        estimated_wait_minutes=turnaround_mins,
        price_breakdown=pricing,
        model_info=model_info,
        processing_time_ms=duration_ms,
    )


# -------------------------------------------------------------
# 5. Smart Billing & Shop Price Configuration (SQLite)
# -------------------------------------------------------------
@app.get("/api/pricing/", response_model=PricingConfigModel)
def get_pricing() -> dict[str, Any]:
    """Retrieves current persistent shop rate card from SQLite database."""
    return get_pricing_config()


@app.put("/api/pricing/", response_model=PricingConfigModel)
def update_pricing(config: PricingConfigModel) -> dict[str, Any]:
    """Updates persistent shop rates in SQLite database.

    Args:
        config: PricingConfigModel with updated rates.

    Returns:
        Updated pricing rate dictionary.
    """
    return update_pricing_config(config.model_dump())


@app.post("/api/billing/calculate/", response_model=BillingCalculationResponse)
def calculate_billing(req: BillingCalculationRequest) -> BillingCalculationResponse:
    """Calculates deterministic order totals using persistent shop rate card.

    Args:
        req: BillingCalculationRequest containing line items.

    Returns:
        BillingCalculationResponse with grand total and itemized breakdown.
    """
    pricing = get_pricing_config()
    items_dicts = [i.model_dump() for i in req.items]
    result = calculate_order_total(items_dicts, pricing)
    return BillingCalculationResponse(
        items=result["items"],
        total_sheets=result["total_sheets"],
        grand_total=result["grand_total"],
        currency=result["currency"],
    )


# -------------------------------------------------------------
# 6. AI Order Assistant (Gemma 2:2B + Heuristic Guardrail)
# -------------------------------------------------------------
@app.post("/api/orders/parse-ai/", response_model=OrderParseResponse)
def parse_order_ai(req: OrderParseRequest) -> OrderParseResponse:
    """Parses natural-language counter request and calculates exact billing.

    Args:
        req: OrderParseRequest containing natural text request.

    Returns:
        OrderParseResponse with parsed parameters and deterministic billing.
    """
    parsed, is_fallback, model_used = parse_order_with_ai(req.natural_text)

    pricing = get_pricing_config()
    billing_calc = calculate_order_total([parsed], pricing)

    return OrderParseResponse(
        parsed_order=parsed,
        is_fallback=is_fallback,
        model_used=model_used,
        calculated_billing=BillingCalculationResponse(
            items=billing_calc["items"],
            total_sheets=billing_calc["total_sheets"],
            grand_total=billing_calc["grand_total"],
            currency=billing_calc["currency"],
        ),
    )


# -------------------------------------------------------------
# 7. Order Management (Persistent SQLite)
# -------------------------------------------------------------
@app.post("/api/orders/", response_model=OrderResponse)
def create_new_order(req: OrderCreateRequest) -> OrderResponse:
    """Creates and persists a new counter order record.

    Args:
        req: OrderCreateRequest with customer details and line items.

    Returns:
        OrderResponse representing created order record.
    """
    pricing = get_pricing_config()
    items_dicts = [i.model_dump() for i in req.items]
    billing_calc = calculate_order_total(items_dicts, pricing)

    order = create_order(
        customer_name=req.customer_name,
        customer_phone=req.customer_phone or "",
        items=billing_calc["items"],
        total_amount=billing_calc["grand_total"],
        notes=req.notes or "",
        status=req.status or "Pending",
    )
    return OrderResponse(**order)


@app.get("/api/orders/", response_model=list[OrderResponse])
def get_orders(
    status: Optional[str] = Query(
        None, description="Filter by Pending, Processing, Completed, or all"
    ),
    search: Optional[str] = Query(
        None, description="Search by customer name, phone, or order ID"
    ),
    limit: int = Query(50, ge=1, le=200),
) -> list[OrderResponse]:
    """Retrieves paginated orders with optional status or keyword filtering.

    Args:
        status: Optional status filter.
        search: Optional customer or order ID search term.
        limit: Maximum number of records to return.

    Returns:
        List of OrderResponse objects.
    """
    orders = list_orders(status=status, search=search, limit=limit)
    return [OrderResponse(**o) for o in orders]


@app.get("/api/orders/{order_id}", response_model=OrderResponse)
def get_single_order(order_id: str) -> OrderResponse:
    """Retrieves a single order by its public business identifier.

    Args:
        order_id: Unique order ID (e.g. 'XRX-20261119-0001').

    Returns:
        OrderResponse matching the order ID.

    Raises:
        HTTPException: If order ID is not found.
    """
    order = get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found.")
    return OrderResponse(**order)


@app.patch("/api/orders/{order_id}/status", response_model=OrderResponse)
def update_status(order_id: str, req: OrderStatusUpdateRequest) -> OrderResponse:
    """Transitions order status between Pending, Processing, and Completed.

    Args:
        order_id: Unique order identifier.
        req: OrderStatusUpdateRequest with target status.

    Returns:
        Updated OrderResponse.

    Raises:
        HTTPException: If status is invalid or order ID is not found.
    """
    valid_statuses = ["Pending", "Processing", "Completed"]
    if req.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{req.status}'. Must be one of: {valid_statuses}",
        )
    order = update_order_status(order_id, req.status)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found.")
    return OrderResponse(**order)


# -------------------------------------------------------------
# 8. Sentry & Observability Telemetry Monitor
# -------------------------------------------------------------
@app.get("/api/telemetry/")
def get_telemetry() -> dict[str, Any]:
    """Returns real-time pipeline telemetry spans and engine status for dashboard."""
    return {
        "recent_spans": get_recent_telemetry(),
        "tabpfn_status": {
            "engine": estimator_engine.engine_name,
            "is_native": estimator_engine.is_tabpfn_loaded,
        },
        "gemma_status": {
            "model": settings.GEMMA_MODEL,
            "ollama_endpoint": settings.OLLAMA_BASE_URL,
        },
    }
