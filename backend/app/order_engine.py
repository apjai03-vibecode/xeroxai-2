"""AI Order Assistant and Deterministic Smart Billing Engine for XeroxAI 2.0.

Provides natural-language order parsing (Ollama Gemma with heuristic regex fallback)
and deterministic counter rate calculation based on persistent SQLite rate cards.
"""

import json
import logging
import math
import re
from typing import Any, Optional
import httpx

from app.config import settings
from app.database import get_pricing_config
from app.telemetry import trace_span

logger = logging.getLogger(__name__)

ORDER_PARSER_SYSTEM_PROMPT: str = """
You are XeroxAI, an intelligent print shop assistant.
Parse the counter operator's natural language print request into structured order parameters.
Return ONLY valid JSON with this exact schema:
{
  "customer_name": "string (default: 'Walk-in Customer')",
  "customer_phone": "string (empty if not specified)",
  "page_count": 1,
  "is_color": false,
  "is_double_sided": false,
  "paper_size": "A4",
  "copies": 1,
  "needs_lamination": false,
  "notes": "string"
}
Rules:
- paper_size must be one of: "A4", "A3", "Legal", "Letter"
- is_color is true if color/colour is requested, false if black and white or not mentioned
- is_double_sided is true if back-to-back, duplex, or double-sided is requested
- DO NOT invent, generate, or calculate any prices. Return parameters only.
"""


def _extract_copies(raw: str) -> tuple[int, bool]:
    """Extracts requested copy or set count from natural language string.

    Args:
        raw: Customer request text.

    Returns:
        Tuple of (copy_count_integer, matched_boolean).
    """
    match = re.search(
        r"(\d+)\s*(?:(?:colour|color|bw|b&w)\s+)?(?:copies|sets|prints|copy)\b",
        raw,
        re.I,
    )
    if match:
        return int(match.group(1)), True
    return 1, False


def _extract_page_count(raw: str, copies_matched: bool, copies: int) -> int:
    """Extracts document page count from natural language text.

    Args:
        raw: Customer request text.
        copies_matched: Whether copies count was explicitly parsed.
        copies: Previously parsed copies count.

    Returns:
        Page count integer (at least 1).
    """
    match = re.search(r"(\d+)\s*(?:pages|page|pgs|pg|sheets|sheet)", raw, re.I)
    if match:
        return int(match.group(1))

    num_matches = re.findall(r"\b\d+\b", raw)
    if len(num_matches) > 1 and copies_matched:
        other = [int(n) for n in num_matches if int(n) != copies]
        return other[0] if other else 1
    if num_matches and not copies_matched:
        return int(num_matches[0])
    return 1


def _extract_paper_size(raw: str) -> str:
    """Determines target paper size from natural language text.

    Args:
        raw: Customer request text.

    Returns:
        Standard paper size string ('A4', 'A3', 'Legal', or 'Letter').
    """
    if re.search(r"\bA3\b", raw, re.I):
        return "A3"
    if re.search(r"\blegal\b", raw, re.I):
        return "Legal"
    if re.search(r"\bletter\b", raw, re.I):
        return "Letter"
    return "A4"


def _extract_customer_info(raw: str) -> tuple[str, str]:
    """Extracts customer name and contact phone from counter string.

    Args:
        raw: Customer request text.

    Returns:
        Tuple of (customer_name_string, customer_phone_string).
    """
    name_match = re.search(r"\bfor\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)\b", raw, re.I)
    if not name_match:
        name_match = re.search(
            r"(?:name|customer)\s*[:=]\s*([A-Za-z]+(?:\s+[A-Za-z]+)?)", raw, re.I
        )

    customer_name = name_match.group(1).strip() if name_match else "Walk-in Customer"
    reserved_words = {
        "customer",
        "print",
        "copies",
        "a4",
        "color",
        "wants",
        "needs",
        "please",
    }
    if customer_name.lower() in reserved_words:
        customer_name = "Walk-in Customer"

    phone_match = re.search(
        r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b[6-9]\d{9}\b",
        raw,
    )
    customer_phone = phone_match.group(0).strip() if phone_match else ""
    return customer_name, customer_phone


def heuristic_parse_order(text: str) -> dict[str, Any]:
    """Deterministic rule-based parser for counter operators when Ollama is offline.

    Extracts copies, page count, color, sides, paper size, and lamination using regex.

    Args:
        text: Counter customer request text string.

    Returns:
        Dictionary of validated order parameters.
    """
    raw = text.strip()
    copies, copies_matched = _extract_copies(raw)
    page_count = _extract_page_count(raw, copies_matched, copies)
    is_color = bool(re.search(r"\b(color|colour|multicolor|rgb)\b", raw, re.I))
    is_double_sided = bool(
        re.search(
            r"\b(double|duplex|back[- ]to[- ]back|both[- ]sides?|2[- ]sided)\b",
            raw,
            re.I,
        )
    )
    paper_size = _extract_paper_size(raw)
    needs_lamination = bool(re.search(r"\b(laminat\w*|lamination|pouch)\b", raw, re.I))
    customer_name, customer_phone = _extract_customer_info(raw)

    return {
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "page_count": max(1, page_count),
        "is_color": is_color,
        "is_double_sided": is_double_sided,
        "paper_size": paper_size,
        "copies": max(1, copies),
        "needs_lamination": needs_lamination,
        "notes": raw,
    }


def parse_order_with_ai(natural_text: str) -> tuple[dict[str, Any], bool, str]:
    """Parses natural-language counter request using Gemma 2:2B with heuristic fallback.

    Args:
        natural_text: Informal customer request entered by operator.

    Returns:
        Tuple of (parsed_parameter_dict, is_fallback_boolean, model_identifier_string).
    """
    with trace_span(
        op="llm.order_parsing",
        description=f"Parse print order using {settings.GEMMA_MODEL}",
        tags={"model": settings.GEMMA_MODEL},
        data={"input_len": len(natural_text)},
    ):
        try:
            payload = {
                "model": settings.GEMMA_MODEL,
                "prompt": f"{ORDER_PARSER_SYSTEM_PROMPT}\n\nCustomer Request: {natural_text}",
                "format": "json",
                "stream": False,
                "options": {"temperature": 0.1},
            }
            res = httpx.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=settings.OLLAMA_TIMEOUT_SECONDS,
            )
            if res.status_code == 200:
                parsed = json.loads(res.json().get("response", "{}"))
                clean_params: dict[str, Any] = {
                    "customer_name": str(
                        parsed.get("customer_name") or "Walk-in Customer"
                    ),
                    "customer_phone": str(parsed.get("customer_phone") or ""),
                    "page_count": max(1, int(parsed.get("page_count", 1))),
                    "is_color": bool(parsed.get("is_color", False)),
                    "is_double_sided": bool(parsed.get("is_double_sided", False)),
                    "paper_size": str(
                        parsed.get("paper_size")
                        if parsed.get("paper_size") in ["A4", "A3", "Legal", "Letter"]
                        else "A4"
                    ),
                    "copies": max(1, int(parsed.get("copies", 1))),
                    "needs_lamination": bool(parsed.get("needs_lamination", False)),
                    "notes": str(parsed.get("notes") or natural_text),
                }
                return clean_params, False, f"{settings.GEMMA_MODEL} (Live Ollama)"

            logger.warning(
                "Ollama responded with status %d; falling back to heuristic order parser.",
                res.status_code,
            )
            return heuristic_parse_order(natural_text), True, "Heuristic Rule Fallback"
        except (httpx.HTTPError, json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.info(
                "Ollama unavailable or response invalid (%s); using heuristic fallback.",
                exc,
            )
            return heuristic_parse_order(natural_text), True, "Heuristic Rule Fallback"


def calculate_item_cost(
    page_count: int,
    is_color: bool,
    is_double_sided: bool,
    paper_size: str,
    copies: int = 1,
    needs_lamination: bool = False,
    pricing: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Calculates deterministic itemized cost using persistent shop rates.

    AI never generates or alters pricing; rate cards govern all totals.

    Args:
        page_count: Total pages in the document.
        is_color: Whether color printing was chosen.
        is_double_sided: Whether duplex printing was requested.
        paper_size: Selected paper size ('A4', 'A3', 'Legal', or 'Letter').
        copies: Number of identical copies requested.
        needs_lamination: Whether lamination finishing is added.
        pricing: Optional pricing dictionary. If omitted, fetched from SQLite.

    Returns:
        Dictionary containing itemized description, sheet count, unit rate, and subtotal.
    """
    cfg = pricing or get_pricing_config()

    size_lower = paper_size.lower()
    if size_lower == "a3":
        paper_mult = float(cfg.get("a3_multiplier", 2.0))
        lamination_rate = float(cfg.get("lamination_a3", 40.0))
    elif size_lower == "legal":
        paper_mult = float(cfg.get("legal_multiplier", 1.25))
        lamination_rate = float(cfg.get("lamination_a4", 20.0))
    elif size_lower == "letter":
        paper_mult = float(cfg.get("letter_multiplier", 1.0))
        lamination_rate = float(cfg.get("lamination_a4", 20.0))
    else:  # A4
        paper_mult = 1.0
        lamination_rate = float(cfg.get("lamination_a4", 20.0))

    if is_color:
        single_rate = float(cfg.get("color_single", 10.0))
        double_rate = float(cfg.get("color_double", 16.0))
    else:
        single_rate = float(cfg.get("bw_single", 2.0))
        double_rate = float(cfg.get("bw_double", 3.0))

    single_unit_price = round(single_rate * paper_mult, 2)
    double_unit_price = round(double_rate * paper_mult, 2)

    if is_double_sided:
        sheets = math.ceil(page_count / 2)
        full_duplex_sheets = page_count // 2
        odd_single_page = page_count % 2
        print_cost_per_copy = (full_duplex_sheets * double_unit_price) + (
            odd_single_page * single_unit_price
        )
    else:
        sheets = page_count
        print_cost_per_copy = page_count * single_unit_price

    total_print_cost = round(print_cost_per_copy * copies, 2)
    lamination_cost = round((lamination_rate * copies) if needs_lamination else 0.0, 2)
    subtotal = round(total_print_cost + lamination_cost, 2)

    description = (
        f"{page_count} page(s) {paper_size} {'Color' if is_color else 'B&W'} "
        f"{'Double-sided' if is_double_sided else 'Single-sided'} ({copies} cop{'ies' if copies > 1 else 'y'})"
    )
    if needs_lamination:
        description += " + Lamination"

    return {
        "description": description,
        "page_count": page_count,
        "sheets": sheets,
        "copies": copies,
        "paper_size": paper_size,
        "is_color": is_color,
        "is_double_sided": is_double_sided,
        "needs_lamination": needs_lamination,
        "unit_rate": double_unit_price if is_double_sided else single_unit_price,
        "print_cost": total_print_cost,
        "lamination_cost": lamination_cost,
        "subtotal": subtotal,
    }


def calculate_order_total(
    items: list[dict[str, Any]], pricing: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """Calculates order totals across multiple line items.

    Args:
        items: List of line-item specification dictionaries.
        pricing: Optional pricing rate card dictionary.

    Returns:
        Order calculation summary dictionary containing line items, total sheets, and grand total.
    """
    processed_items: list[dict[str, Any]] = []
    grand_total = 0.0
    total_sheets = 0

    for item in items:
        calc = calculate_item_cost(
            page_count=int(item.get("page_count", 1)),
            is_color=bool(item.get("is_color", False)),
            is_double_sided=bool(item.get("is_double_sided", False)),
            paper_size=str(item.get("paper_size", "A4")),
            copies=int(item.get("copies", 1)),
            needs_lamination=bool(item.get("needs_lamination", False)),
            pricing=pricing,
        )
        processed_items.append(calc)
        grand_total += calc["subtotal"]
        total_sheets += calc["sheets"] * calc["copies"]

    return {
        "items": processed_items,
        "total_sheets": total_sheets,
        "grand_total": round(grand_total, 2),
        "currency": "INR",
    }
