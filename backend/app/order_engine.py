import json
import math
import re
from typing import Any, Dict, List, Optional, Tuple
import httpx

from app.config import settings
from app.database import get_pricing_config
from app.telemetry import trace_span

ORDER_PARSER_SYSTEM_PROMPT = """
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

def heuristic_parse_order(text: str) -> Dict[str, Any]:
    """
    Deterministic rule-based parser for counter operators when Ollama is offline.
    Extracts copies, page count, color, sides, paper size, and lamination.
    """
    raw = text.strip()
    
    # 1. Copies (handles "50 copies", "50 colour copies", "3 sets")
    copies_match = re.search(r'(\d+)\s*(?:(?:colour|color|bw|b&w)\s+)?(?:copies|sets|prints|copy)\b', raw, re.I)
    copies = int(copies_match.group(1)) if copies_match else 1
    
    # 2. Page count
    pages_match = re.search(r'(\d+)\s*(?:pages|page|pgs|pg|sheets|sheet)', raw, re.I)
    if pages_match:
        page_count = int(pages_match.group(1))
    else:
        # Check standalone number if copies was already captured
        num_matches = re.findall(r'\b\d+\b', raw)
        if len(num_matches) > 1 and copies_match:
            # Take the other number
            other = [int(n) for n in num_matches if int(n) != copies]
            page_count = other[0] if other else 1
        elif num_matches and not copies_match:
            page_count = int(num_matches[0])
        else:
            page_count = 1
            
    # 3. Color vs B&W
    is_color = bool(re.search(r'\b(color|colour|multicolor|rgb)\b', raw, re.I))
    
    # 4. Double sided vs Single sided
    is_double_sided = bool(re.search(r'\b(double|duplex|back[- ]to[- ]back|both[- ]sides?|2[- ]sided)\b', raw, re.I))
    
    # 5. Paper size
    paper_size = "A4"
    if re.search(r'\bA3\b', raw, re.I):
        paper_size = "A3"
    elif re.search(r'\blegal\b', raw, re.I):
        paper_size = "Legal"
    elif re.search(r'\bletter\b', raw, re.I):
        paper_size = "Letter"
        
    # 6. Lamination
    needs_lamination = bool(re.search(r'\b(laminat\w*|lamination|pouch)\b', raw, re.I))
    
    # 7. Customer info
    name_match = re.search(r'\bfor\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)\b', raw, re.I)
    if not name_match:
        name_match = re.search(r'(?:name|customer)\s*[:=]\s*([A-Za-z]+(?:\s+[A-Za-z]+)?)', raw, re.I)
    customer_name = name_match.group(1).strip() if name_match else "Walk-in Customer"
    if customer_name.lower() in ["customer", "print", "copies", "a4", "color", "wants", "needs", "please"]:
        customer_name = "Walk-in Customer"
        
    phone_match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b[6-9]\d{9}\b', raw)
    customer_phone = phone_match.group(0).strip() if phone_match else ""
    
    return {
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "page_count": max(1, page_count),
        "is_color": is_color,
        "is_double_sided": is_double_sided,
        "paper_size": paper_size,
        "copies": max(1, copies),
        "needs_lamination": needs_lamination,
        "notes": raw
    }

def parse_order_with_ai(natural_text: str) -> Tuple[Dict[str, Any], bool, str]:
    """
    Parses natural language order request using Gemma 2:2B with heuristic fallback.
    Returns: (parsed_dict, is_fallback, model_info)
    """
    with trace_span(
        op="llm.order_parsing",
        description=f"Parse print order using {settings.GEMMA_MODEL}",
        tags={"model": settings.GEMMA_MODEL},
        data={"input_len": len(natural_text)}
    ):
        try:
            payload = {
                "model": settings.GEMMA_MODEL,
                "prompt": f"{ORDER_PARSER_SYSTEM_PROMPT}\n\nCustomer Request: {natural_text}",
                "format": "json",
                "stream": False,
                "options": {"temperature": 0.1}
            }
            res = httpx.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=settings.OLLAMA_TIMEOUT_SECONDS
            )
            if res.status_code == 200:
                parsed = json.loads(res.json().get("response", "{}"))
                # Sanitize fields
                clean_params = {
                    "customer_name": str(parsed.get("customer_name") or "Walk-in Customer"),
                    "customer_phone": str(parsed.get("customer_phone") or ""),
                    "page_count": max(1, int(parsed.get("page_count", 1))),
                    "is_color": bool(parsed.get("is_color", False)),
                    "is_double_sided": bool(parsed.get("is_double_sided", False)),
                    "paper_size": str(parsed.get("paper_size") if parsed.get("paper_size") in ["A4", "A3", "Legal", "Letter"] else "A4"),
                    "copies": max(1, int(parsed.get("copies", 1))),
                    "needs_lamination": bool(parsed.get("needs_lamination", False)),
                    "notes": str(parsed.get("notes") or natural_text)
                }
                return clean_params, False, f"{settings.GEMMA_MODEL} (Live Ollama)"
            else:
                return heuristic_parse_order(natural_text), True, "Heuristic Rule Fallback"
        except Exception:
            return heuristic_parse_order(natural_text), True, "Heuristic Rule Fallback"

def calculate_item_cost(
    page_count: int,
    is_color: bool,
    is_double_sided: bool,
    paper_size: str,
    copies: int = 1,
    needs_lamination: bool = False,
    pricing: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Deterministic Smart Billing calculation based on persistent shop rates.
    AI NEVER determines or alters prices.
    """
    cfg = pricing or get_pricing_config()
    
    # 1. Paper size multiplier
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
        
    # 2. Base sheet rate
    if is_color:
        single_rate = float(cfg.get("color_single", 10.0))
        double_rate = float(cfg.get("color_double", 16.0))
    else:
        single_rate = float(cfg.get("bw_single", 2.0))
        double_rate = float(cfg.get("bw_double", 3.0))
        
    single_unit_price = round(single_rate * paper_mult, 2)
    double_unit_price = round(double_rate * paper_mult, 2)
    
    # 3. Calculate printing charge per copy
    if is_double_sided:
        # Pairs of pages printed back-to-back on one sheet
        sheets = math.ceil(page_count / 2)
        full_duplex_sheets = page_count // 2
        odd_single_page = page_count % 2
        print_cost_per_copy = (full_duplex_sheets * double_unit_price) + (odd_single_page * single_unit_price)
    else:
        sheets = page_count
        print_cost_per_copy = page_count * single_unit_price
        
    total_print_cost = round(print_cost_per_copy * copies, 2)
    
    # 4. Lamination
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
        "subtotal": subtotal
    }

def calculate_order_total(items: List[Dict[str, Any]], pricing: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Calculates full order totals across all line items."""
    processed_items = []
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
            pricing=pricing
        )
        processed_items.append(calc)
        grand_total += calc["subtotal"]
        total_sheets += calc["sheets"] * calc["copies"]
        
    return {
        "items": processed_items,
        "total_sheets": total_sheets,
        "grand_total": round(grand_total, 2),
        "currency": "INR"
    }
