import io
from typing import Tuple
from PIL import Image, ImageOps
from app.models import PhotoPreset
from app.telemetry import trace_span

# Size constants in bytes
MIN_TNPSC_BYTES = 20 * 1024       # 20,480 bytes
MAX_TNPSC_BYTES = 50 * 1024       # 51,200 bytes
MAX_SIGNATURE_BYTES = 20 * 1024   # 20,480 bytes

def _pad_jpeg_to_range(jpeg_bytes: bytes, min_bytes: int, max_bytes: int) -> bytes:
    """
    Appends a standard JPEG COM (Comment) marker (0xFF 0xFE) to safely increase
    the file size without corrupting standard JPEG decoding or image data,
    guaranteeing strict adherence to government portal minimum upload thresholds.
    """
    current_size = len(jpeg_bytes)
    if current_size >= min_bytes:
        return jpeg_bytes
    
    needed_bytes = min_bytes - current_size + 1024  # Pad safely into the mid-range (e.g. ~25-35KB)
    if current_size + needed_bytes > max_bytes:
        needed_bytes = max_bytes - current_size - 64

    if needed_bytes <= 4:
        return jpeg_bytes

    # Structure of JPEG COM marker:
    # 0xFF 0xFE (marker) + 2-byte big-endian length + payload
    # Length includes the 2 length bytes themselves
    length = min(65535, needed_bytes)
    payload_len = length - 2
    padding_payload = b"XeroxAI-Govt-Pad" + (b"\x00" * max(0, payload_len - 16))
    com_marker = b"\xff\xfe" + length.to_bytes(2, "big") + padding_payload[:payload_len]
    
    # Insert right before EOI (0xFF 0xD9) if present at the end
    if jpeg_bytes.endswith(b"\xff\xd9"):
        return jpeg_bytes[:-2] + com_marker + b"\xff\xd9"
    return jpeg_bytes + com_marker

def process_photo(
    input_bytes: bytes,
    preset: PhotoPreset
) -> Tuple[bytes, dict[str, str]]:
    """
    Processes, resizes, enhances, and dynamically compresses photos
    according to strict official counter specifications.
    
    Returns:
        (image_bytes, metadata_headers_dict)
    """
    with trace_span(
        op="image.processing",
        description=f"Resize and compress photo for {preset.value}",
        tags={"preset": preset.value},
        data={"input_size_bytes": len(input_bytes)}
    ):
        img = Image.open(io.BytesIO(input_bytes))
        
        # Handle orientation if EXIF is present
        img = ImageOps.exif_transpose(img)
        
        # Convert to RGB for universal JPEG output
        if img.mode != "RGB":
            img = img.convert("RGB")
            
        final_dimensions = ""
        output_io = io.BytesIO()
        
        if preset == PhotoPreset.TNPSC_UPSC:
            # 1. Resize strictly to 200x230 px
            target_w, target_h = 200, 230
            resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            final_dimensions = f"{target_w}x{target_h}"
            
            # 2. Dynamic compression quality from 85 down to 50
            # Target size strictly between 20 KB and 50 KB
            best_bytes = b""
            for quality in range(85, 49, -5):
                buf = io.BytesIO()
                resized.save(buf, format="JPEG", quality=quality, optimize=True)
                b = buf.getvalue()
                if len(b) <= MAX_TNPSC_BYTES:
                    best_bytes = b
                    break
            
            if not best_bytes:
                # If quality 50 was still > 50KB (extremely rare at 200x230), lower further
                buf = io.BytesIO()
                resized.save(buf, format="JPEG", quality=40, optimize=True)
                best_bytes = buf.getvalue()
            
            # Ensure strictly >= 20 KB
            if len(best_bytes) < MIN_TNPSC_BYTES:
                best_bytes = _pad_jpeg_to_range(best_bytes, MIN_TNPSC_BYTES, MAX_TNPSC_BYTES)
                
            final_bytes = best_bytes
            
        elif preset == PhotoPreset.PASSPORT_STANDARD:
            # 35x45 mm ratio -> 413x531 px at 300 DPI
            target_w, target_h = 413, 531
            final_dimensions = f"{target_w}x{target_h}"
            
            # Auto-contrast enhancement for crisp counter printing
            enhanced = ImageOps.autocontrast(img, cutoff=1)
            resized = enhanced.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            buf = io.BytesIO()
            resized.save(buf, format="JPEG", quality=92, optimize=True, dpi=(300, 300))
            final_bytes = buf.getvalue()
            
        elif preset == PhotoPreset.SIGNATURE:
            # Strictly 140x60 px, strictly under 20 KB
            target_w, target_h = 140, 60
            final_dimensions = f"{target_w}x{target_h}"
            
            # Auto-contrast to clean up faint ink on counter scans
            enhanced = ImageOps.autocontrast(img, cutoff=2)
            resized = enhanced.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            best_bytes = b""
            for quality in [90, 80, 70, 60, 50, 40]:
                buf = io.BytesIO()
                resized.save(buf, format="JPEG", quality=quality, optimize=True)
                b = buf.getvalue()
                if len(b) < MAX_SIGNATURE_BYTES:
                    best_bytes = b
                    break
            if not best_bytes:
                buf = io.BytesIO()
                resized.save(buf, format="JPEG", quality=30, optimize=True)
                best_bytes = buf.getvalue()
                
            final_bytes = best_bytes
            
        else:
            raise ValueError(f"Unsupported preset: {preset}")
            
        size_kb = round(len(final_bytes) / 1024, 2)
        headers = {
            "X-Dimensions": final_dimensions,
            "X-File-Size-KB": str(size_kb),
            "X-Preset-Applied": preset.value,
            "Content-Disposition": f'attachment; filename="xeroxai_{preset.value}.jpg"'
        }
        
        return final_bytes, headers
