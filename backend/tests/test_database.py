import os
import tempfile
import pytest
from app.database import (
    init_db,
    get_pricing_config,
    update_pricing_config,
    create_order,
    get_order_by_id,
    list_orders,
    update_order_status
)

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_default_pricing_config(temp_db):
    cfg = get_pricing_config(temp_db)
    assert cfg["bw_single"] == 2.0
    assert cfg["bw_double"] == 3.0
    assert cfg["color_single"] == 10.0
    assert cfg["color_double"] == 16.0
    assert cfg["lamination_a4"] == 20.0

def test_update_pricing_config(temp_db):
    updated = update_pricing_config({
        "bw_single": 2.5,
        "bw_double": 4.0,
        "color_single": 12.0,
        "color_double": 18.0,
        "a3_multiplier": 2.2,
        "legal_multiplier": 1.3,
        "letter_multiplier": 1.0,
        "lamination_a4": 25.0,
        "lamination_a3": 45.0
    }, db_path=temp_db)
    
    assert updated["bw_single"] == 2.5
    assert updated["color_single"] == 12.0
    assert updated["lamination_a4"] == 25.0

def test_create_and_get_order(temp_db):
    items = [
        {"desc": "20 pages B&W Double-sided A4", "qty": 20, "price": 60.0},
        {"desc": "Front lamination", "qty": 1, "price": 20.0}
    ]
    order = create_order(
        customer_name="Vijay Kumar",
        customer_phone="9876543210",
        items=items,
        total_amount=80.0,
        notes="Urgent exam print",
        db_path=temp_db
    )
    
    assert order["order_id"].startswith("XRX-")
    assert order["customer_name"] == "Vijay Kumar"
    assert order["total_amount"] == 80.0
    assert order["status"] == "Pending"
    assert len(order["items"]) == 2
    
    fetched = get_order_by_id(order["order_id"], db_path=temp_db)
    assert fetched is not None
    assert fetched["customer_name"] == "Vijay Kumar"

def test_list_and_update_orders(temp_db):
    create_order("Customer A", [{"item": 1}], 20.0, db_path=temp_db)
    o2 = create_order("Customer B", [{"item": 2}], 45.0, db_path=temp_db)
    
    orders = list_orders(db_path=temp_db)
    assert len(orders) == 2
    
    updated = update_order_status(o2["order_id"], "Completed", db_path=temp_db)
    assert updated["status"] == "Completed"
    
    pending_only = list_orders(status="Pending", db_path=temp_db)
    assert len(pending_only) == 1
    assert pending_only[0]["customer_name"] == "Customer A"
    
    search_res = list_orders(search="Customer B", db_path=temp_db)
    assert len(search_res) == 1
    assert search_res[0]["order_id"] == o2["order_id"]
