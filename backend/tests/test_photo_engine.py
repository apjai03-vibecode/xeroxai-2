import io
import pytest
from PIL import Image
from app.models import PhotoPreset
from app.photo_engine import process_photo, MIN_TNPSC_BYTES, MAX_TNPSC_BYTES, MAX_SIGNATURE_BYTES

def _create_test_image(width: int, height: int, pattern: str = "gradient") -> bytes:
    """Helper to generate in-memory synthetic images for testing."""
    img = Image.new("RGB", (width, height), color=(240, 240, 240))
    if pattern == "gradient":
        # Add varying pixel details to simulate real photos
        for x in range(width):
            for y in range(height):
                img.putpixel((x, y), (x % 255, y % 255, (x * y) % 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()

def test_tnpsc_upsc_preset_dimensions_and_size_bounds():
    """TNPSC/UPSC photo must strictly be 200x230 px and 20KB <= size <= 50KB."""
    # Test with standard detailed image
    test_img_bytes = _create_test_image(800, 1000, pattern="gradient")
    processed_bytes, headers = process_photo(test_img_bytes, PhotoPreset.TNPSC_UPSC)
    
    assert headers["X-Dimensions"] == "200x230"
    assert headers["X-Preset-Applied"] == "tnpsc_upsc"
    
    # Verify resulting image dimensions
    out_img = Image.open(io.BytesIO(processed_bytes))
    assert out_img.size == (200, 230)
    
    # Verify strict size bounds: 20 KB <= size <= 50 KB
    file_size = len(processed_bytes)
    assert file_size >= MIN_TNPSC_BYTES, f"File size {file_size} is under 20KB threshold"
    assert file_size <= MAX_TNPSC_BYTES, f"File size {file_size} exceeds 50KB threshold"

def test_tnpsc_upsc_preset_with_flat_image():
    """Even with flat/simple images, padding logic must guarantee >= 20KB and <= 50KB."""
    flat_img = Image.new("RGB", (400, 500), color=(255, 255, 255))
    buf = io.BytesIO()
    flat_img.save(buf, format="JPEG", quality=80)
    
    processed_bytes, headers = process_photo(buf.getvalue(), PhotoPreset.TNPSC_UPSC)
    out_img = Image.open(io.BytesIO(processed_bytes))
    assert out_img.size == (200, 230)
    
    file_size = len(processed_bytes)
    assert file_size >= MIN_TNPSC_BYTES, f"Flat image size {file_size} is under 20KB"
    assert file_size <= MAX_TNPSC_BYTES, f"Flat image size {file_size} exceeds 50KB"

def test_passport_standard_preset():
    """Passport standard must be 413x531 px (35x45mm at 300 DPI)."""
    test_img = _create_test_image(600, 800)
    processed_bytes, headers = process_photo(test_img, PhotoPreset.PASSPORT_STANDARD)
    
    assert headers["X-Dimensions"] == "413x531"
    out_img = Image.open(io.BytesIO(processed_bytes))
    assert out_img.size == (413, 531)

def test_signature_preset():
    """Signature must strictly be 140x60 px and strictly under 20KB."""
    test_img = _create_test_image(500, 300)
    processed_bytes, headers = process_photo(test_img, PhotoPreset.SIGNATURE)
    
    assert headers["X-Dimensions"] == "140x60"
    out_img = Image.open(io.BytesIO(processed_bytes))
    assert out_img.size == (140, 60)
    
    file_size = len(processed_bytes)
    assert file_size < MAX_SIGNATURE_BYTES, f"Signature file size {file_size} is not under 20KB"
