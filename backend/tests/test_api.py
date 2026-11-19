import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from PIL import Image

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "sponsor_integrations" in data
    assert "gemma" in data["sponsor_integrations"]
    assert "tabpfn" in data["sponsor_integrations"]
    assert "sentry" in data["sponsor_integrations"]
    assert "features" in data
    assert "smartdoc_ai" in data["features"]

def test_resize_photo_api_tnpsc():
    img = Image.new("RGB", (500, 600), color=(180, 200, 220))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    
    files = {"file": ("test.jpg", buf.getvalue(), "image/jpeg")}
    data = {"preset": "tnpsc_upsc"}
    
    response = client.post("/api/resize-photo/", files=files, data=data)
    assert response.status_code == 200
    assert response.headers["X-Dimensions"] == "200x230"
    size_kb = float(response.headers["X-File-Size-KB"])
    assert 20.0 <= size_kb <= 50.0

def test_generate_biodata_api():
    payload = {
        "raw_text": "Kavitha R, DOB 20/05/2000, MCA from Anna University, 9876501234, kavitha@mail.com, Skills: Python, SQL"
    }
    response = client.post("/api/generate-biodata/", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert "extracted_data" in res_data
    assert res_data["extracted_data"]["full_name"] != ""
    assert res_data["pdf_base64"] is not None

def test_estimate_job_api():
    payload = {
        "page_count": 25,
        "is_color": True,
        "needs_lamination": True,
        "current_queue_customers": 2
    }
    response = client.post("/api/estimate-job/", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["estimated_wait_minutes"] > 0
    assert res_data["price_breakdown"]["total_fee"] > 0
    assert "model_info" in res_data

def test_telemetry_api():
    response = client.get("/api/telemetry/")
    assert response.status_code == 200
    data = response.json()
    assert "recent_spans" in data
    assert "tabpfn_status" in data
    assert "gemma_status" in data

def test_smartdoc_enhance_api():
    img = Image.new("RGB", (600, 800), color=(240, 240, 240))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    
    files = {"file": ("doc.jpg", buf.getvalue(), "image/jpeg")}
    data = {
        "output_mode": "enhanced_color",
        "auto_deskew": "true",
        "auto_perspective": "true",
        "remove_shadows": "true"
    }
    response = client.post("/api/smartdoc/enhance/", files=files, data=data)
    assert response.status_code == 200
    res_data = response.json()
    assert "original_preview_base64" in res_data
    assert "processed_preview_base64" in res_data
    assert res_data["width"] > 0
    assert len(res_data["reliability_notes"]) >= 1

def test_pricing_and_billing_api():
    # 1. Get pricing
    res = client.get("/api/pricing/")
    assert res.status_code == 200
    cfg = res.json()
    assert cfg["bw_single"] > 0
    
    # 2. Calculate billing
    calc_payload = {
        "items": [
            {
                "page_count": 10,
                "is_color": False,
                "is_double_sided": True,
                "paper_size": "A4",
                "copies": 2,
                "needs_lamination": False
            }
        ]
    }
    calc_res = client.post("/api/billing/calculate/", json=calc_payload)
    assert calc_res.status_code == 200
    b_data = calc_res.json()
    assert b_data["grand_total"] > 0
    assert b_data["total_sheets"] == 10

def test_order_lifecycle_api():
    # 1. Create order
    order_payload = {
        "customer_name": "Deepak Raj",
        "customer_phone": "9876543210",
        "items": [
            {
                "page_count": 5,
                "is_color": True,
                "is_double_sided": False,
                "paper_size": "A4",
                "copies": 1,
                "needs_lamination": True
            }
        ],
        "notes": "Color print with front lamination"
    }
    create_res = client.post("/api/orders/", json=order_payload)
    assert create_res.status_code == 200
    order = create_res.json()
    order_id = order["order_id"]
    assert order["status"] == "Pending"
    assert order["total_amount"] > 0
    
    # 2. Get single order
    get_res = client.get(f"/api/orders/{order_id}")
    assert get_res.status_code == 200
    assert get_res.json()["customer_name"] == "Deepak Raj"
    
    # 3. Update status
    patch_res = client.patch(f"/api/orders/{order_id}/status", json={"status": "Processing"})
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "Processing"
    
    # 4. List orders
    list_res = client.get("/api/orders/?status=Processing")
    assert list_res.status_code == 200
    assert any(o["order_id"] == order_id for o in list_res.json())

def test_parse_order_ai_api():
    payload = {
        "natural_text": "20 copies of 2 page A4 color single-sided with lamination for Vignesh"
    }
    response = client.post("/api/orders/parse-ai/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "parsed_order" in data
    assert "calculated_billing" in data
    assert data["calculated_billing"]["grand_total"] > 0
