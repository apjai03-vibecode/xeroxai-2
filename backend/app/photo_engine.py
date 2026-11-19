"""Photo Specification Engine for XeroxAI 2.0.

Provides strict dimensional resizing, contrast tuning, and dynamic compression
for government exam portals (TNPSC/UPSC), standard passports, and counter signature crops.
"""

import io
import logging
from PIL import Image, ImageOps

from app.models import PhotoPreset
from app.telemetry import trace_span

logger = logging.getLogger(__name__)

# Size constants in bytes
MIN_TNPSC_BYTES: int = 20 * 1024  # 20,480 bytes
MAX_TNPSC_BYTES: int = 50 * 1024  # 51,200 bytes
MAX_SIGNATURE_BYTES: int = 20 * 1024  # 20,480 bytes


def _pad_jpeg_to_range(jpeg_bytes: bytes, min_bytes: int, max_bytes: int) -> bytes:
    """Appends a standard JPEG COM (Comment) marker to satisfy minimum byte limits.

    Structure of COM marker: 0xFF 0xFE + 2-byte big-endian length + payload.
    Inserted right before EOI (0xFF 0xD9) so standard JPEG decoders remain unharmed.

    Args:
        jpeg_bytes: Valid JPEG image byte string.
        min_bytes: Minimum byte threshold required by upload portal.
        max_bytes: Maximum byte boundary that must not be exceeded.

    Returns:
        Padded JPEG byte string adhering to portal limits.
    """
    current_size = len(jpeg_bytes)
    if current_size >= min_bytes:
        return jpeg_bytes

    needed_bytes = min_bytes - current_size + 1024  # Pad safely into the mid-range
    if current_size + needed_bytes > max_bytes:
        needed_bytes = max_bytes - current_size - 64

    if needed_bytes <= 4:
        return jpeg_bytes

    length = min(65535, needed_bytes)
    payload_len = length - 2
    padding_payload = b"XeroxAI-Govt-Pad" + (b"\x00" * max(0, payload_len - 16))
    com_marker = b"\xff\xfe" + length.to_bytes(2, "big") + padding_payload[:payload_len]

    if jpeg_bytes.endswith(b"\xff\xd9"):
        return jpeg_bytes[:-2] + com_marker + b"\xff\xd9"
    return jpeg_bytes + com_marker


def _process_tnpsc_upsc(img: Image.Image) -> tuple[bytes, str]:
    """Resizes and dynamically compresses image to strict 200x230 px and 20-50 KB.

    Args:
        img: RGB PIL Image instance.

    Returns:
        Tuple of (compressed_jpeg_bytes, dimensions_string).
    """
    target_w, target_h = 200, 230
    resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    dims_str = f"{target_w}x{target_h}"

    best_bytes = b""
    for quality in range(85, 49, -5):
        buf = io.BytesIO()
        resized.save(buf, format="JPEG", quality=quality, optimize=True)
        b = buf.getvalue()
        if len(b) <= MAX_TNPSC_BYTES:
            best_bytes = b
            break

    if not best_bytes:
        buf = io.BytesIO()
        resized.save(buf, format="JPEG", quality=40, optimize=True)
        best_bytes = buf.getvalue()

    if len(best_bytes) < MIN_TNPSC_BYTES:
        best_bytes = _pad_jpeg_to_range(best_bytes, MIN_TNPSC_BYTES, MAX_TNPSC_BYTES)

    return best_bytes, dims_str


def _process_passport(img: Image.Image) -> tuple[bytes, str]:
    """Enhances and formats image to 35x45 mm ratio (413x531 px at 300 DPI).

    Args:
        img: RGB PIL Image instance.

    Returns:
        Tuple of (compressed_jpeg_bytes, dimensions_string).
    """
    target_w, target_h = 413, 531
    dims_str = f"{target_w}x{target_h}"
    enhanced = ImageOps.autocontrast(img, cutoff=1)
    resized = enhanced.resize((target_w, target_h), Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    resized.save(buf, format="JPEG", quality=92, optimize=True, dpi=(300, 300))
    return buf.getvalue(), dims_str


def _process_signature(img: Image.Image) -> tuple[bytes, str]:
    """Cleans up ink contrast and compresses signature strictly under 20 KB.

    Args:
        img: RGB PIL Image instance.

    Returns:
        Tuple of (compressed_jpeg_bytes, dimensions_string).
    """
    target_w, target_h = 140, 60
    dims_str = f"{target_w}x{target_h}"
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

    return best_bytes, dims_str


def process_photo(
    input_bytes: bytes, preset: PhotoPreset
) -> tuple[bytes, dict[str, str]]:
    """Processes, resizes, and dynamically compresses photos per counter spec.

    Args:
        input_bytes: Raw binary image payload.
        preset: Target preset specification from PhotoPreset enum.

    Returns:
        Tuple of (processed_jpeg_bytes, metadata_headers_dict).

    Raises:
        ValueError: If preset is unsupported or image data is corrupted.
    """
    with trace_span(
        op="image.processing",
        description=f"Resize and compress photo for {preset.value}",
        tags={"preset": preset.value},
        data={"input_size_bytes": len(input_bytes)},
    ):
        img = Image.open(io.BytesIO(input_bytes))
        img = ImageOps.exif_transpose(img)

        if img.mode != "RGB":
            img = img.convert("RGB")

        if preset == PhotoPreset.TNPSC_UPSC:
            final_bytes, final_dimensions = _process_tnpsc_upsc(img)
        elif preset == PhotoPreset.PASSPORT_STANDARD:
            final_bytes, final_dimensions = _process_passport(img)
        elif preset == PhotoPreset.SIGNATURE:
            final_bytes, final_dimensions = _process_signature(img)
        else:
            raise ValueError(f"Unsupported preset: {preset}")

        size_kb = round(len(final_bytes) / 1024, 2)
        headers: dict[str, str] = {
            "X-Dimensions": final_dimensions,
            "X-File-Size-KB": str(size_kb),
            "X-Preset-Applied": preset.value,
            "Content-Disposition": f'attachment; filename="xeroxai_{preset.value}.jpg"',
        }

        return final_bytes, headers
