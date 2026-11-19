import pytest
from app.order_engine import (
    calculate_item_cost,
    calculate_order_total,
    heuristic_parse_order,
    parse_order_with_ai
)

def test_single_sided_bw_calculation():
    # 10 pages B&W single-sided A4 = 10 * 2.0 = 20.0
    res = calculate_item_cost(page_count=10, is_color=False, is_double_sided=False, paper_size="A4", copies=1)
    assert res["print_cost"] == 20.0
    assert res["lamination_cost"] == 0.0
    assert res["subtotal"] == 20.0

def test_double_sided_bw_calculation():
    # 10 pages B&W double-sided A4 = 5 sheets * 3.0 = 15.0
    res = calculate_item_cost(page_count=10, is_color=False, is_double_sided=True, paper_size="A4", copies=1)
    assert res["print_cost"] == 15.0
    assert res["sheets"] == 5
    assert res["subtotal"] == 15.0

def test_odd_page_double_sided():
    # 5 pages B&W double-sided: 2 sheets duplex (2*3=6) + 1 single page (1*2=2) = 8.0
    res = calculate_item_cost(page_count=5, is_color=False, is_double_sided=True, paper_size="A4", copies=1)
    assert res["print_cost"] == 8.0
    assert res["sheets"] == 3

def test_color_and_lamination_with_copies():
    # 2 pages Color single-sided A4 with lamination, 3 copies:
    # Print cost per copy: 2 * 10 = 20 -> 3 copies = 60.0
    # Lamination: 20 * 3 = 60.0
    # Subtotal: 120.0
    res = calculate_item_cost(page_count=2, is_color=True, is_double_sided=False, paper_size="A4", copies=3, needs_lamination=True)
    assert res["print_cost"] == 60.0
    assert res["lamination_cost"] == 60.0
    assert res["subtotal"] == 120.0

def test_a3_multiplier():
    # 1 page B&W single A3: base 2.0 * 2.0 = 4.0
    res = calculate_item_cost(page_count=1, is_color=False, is_double_sided=False, paper_size="A3", copies=1)
    assert res["print_cost"] == 4.0

def test_heuristic_order_parsing():
    text = "Customer wants 50 colour copies, double-sided, and 2 laminated sheets for Rahul phone 9840123456"
    parsed = heuristic_parse_order(text)
    assert parsed["copies"] == 50
    assert parsed["is_color"] is True
    assert parsed["is_double_sided"] is True
    assert parsed["needs_lamination"] is True
    assert "Rahul" in parsed["customer_name"]
    assert "9840123456" in parsed["customer_phone"]

def test_parse_order_with_ai_fallback():
    # Even if Ollama is offline, must return valid parameters without crashing
    res, is_fallback, model = parse_order_with_ai("10 black and white copies single sided A4")
    assert res["page_count"] >= 1
    assert res["paper_size"] == "A4"
    assert res["is_color"] is False
