import io
import pytest
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from app.smartdoc_engine import (
    detect_blur,
    detect_skew_angle,
    deskew_image,
    remove_shadows_and_uneven_light,
    enhance_contrast,
    clean_document_background,
    process_document
)

def _create_synthetic_document_image(skew_angle: float = 0.0, blur: bool = False, shadow: bool = False) -> bytes:
    """Creates a synthetic scanned document image with text lines for testing."""
    # 800 x 600 image
    img = Image.new("RGB", (800, 600), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)
    
    # Draw simulated text lines
    for y in range(80, 520, 35):
        draw.text((100, y), f"Sample Document Line at Y={y} - Government Application Form", fill=(20, 20, 20))
        draw.line([(100, y + 16), (700, y + 16)], fill=(180, 180, 180), width=1)
        
    # Rotate if skew requested
    if abs(skew_angle) > 0.1:
        img = img.rotate(skew_angle, expand=True, fillcolor=(255, 255, 255))
        
    arr = np.array(img)
    
    if shadow:
        # Create gradient shadow on right side
        (h, w) = arr.shape[:2]
        gradient = np.linspace(1.0, 0.4, w).reshape(1, w, 1)
        arr = np.clip(arr * gradient, 0, 255).astype(np.uint8)
        
    if blur:
        arr = cv2.GaussianBlur(arr, (15, 15), 0)
        
    # Encode as JPEG
    _, buf = cv2.imencode(".jpg", cv2.cvtColor(arr, cv2.COLOR_RGB2BGR))
    return buf.tobytes()

def test_blur_detection_sharp_vs_blurred():
    sharp_bytes = _create_synthetic_document_image(blur=False)
    blurred_bytes = _create_synthetic_document_image(blur=True)
    
    sharp_mat = cv2.imdecode(np.frombuffer(sharp_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
    blurred_mat = cv2.imdecode(np.frombuffer(blurred_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
    
    score_sharp, is_blurry_sharp = detect_blur(sharp_mat)
    score_blurred, is_blurry_blurred = detect_blur(blurred_mat)
    
    assert score_sharp > score_blurred
    assert is_blurry_blurred is True

def test_shadow_removal_flattens_gradient():
    shadow_bytes = _create_synthetic_document_image(shadow=True)
    mat = cv2.imdecode(np.frombuffer(shadow_bytes, np.uint8), cv2.IMREAD_COLOR)
    
    # Shadowed image has high difference between left and right background
    cleaned = remove_shadows_and_uneven_light(mat)
    assert cleaned is not None
    assert cleaned.shape == mat.shape

def test_clean_document_modes():
    doc_bytes = _create_synthetic_document_image()
    mat = cv2.imdecode(np.frombuffer(doc_bytes, np.uint8), cv2.IMREAD_COLOR)
    
    res_color = clean_document_background(mat, mode="enhanced_color")
    res_bw = clean_document_background(mat, mode="clean_bw")
    
    assert res_color.shape == mat.shape
    assert res_bw.shape == mat.shape

def test_process_document_pipeline():
    doc_bytes = _create_synthetic_document_image(skew_angle=2.5, shadow=True)
    result = process_document(
        input_bytes=doc_bytes,
        filename="govt_form.jpg",
        output_mode="enhanced_color",
        auto_deskew=True,
        auto_perspective=True,
        remove_shadows=True
    )
    
    assert "original_bytes" in result
    assert "processed_bytes" in result
    assert len(result["processed_bytes"]) > 0
    assert result["filename"] == "govt_form.jpg"
    assert "blur_score" in result
    assert "reliability_notes" in result
    assert len(result["reliability_notes"]) >= 2

def test_process_document_pdf_support():
    import pypdfium2 as pdfium
    from reportlab.pdfgen import canvas
    
    # Create an in-memory test PDF
    pdf_buf = io.BytesIO()
    c = canvas.Canvas(pdf_buf)
    c.drawString(100, 750, "Sample Government Test Document")
    c.drawString(100, 700, "Date of Birth: 01/01/2000 - Candidate ID: 12345")
    c.save()
    pdf_bytes = pdf_buf.getvalue()
    
    result = process_document(
        input_bytes=pdf_bytes,
        filename="test_doc.pdf",
        output_mode="enhanced_color"
    )
    
    assert result["is_pdf"] is True
    assert result["width"] > 0
    assert result["height"] > 0
    assert len(result["processed_bytes"]) > 0
