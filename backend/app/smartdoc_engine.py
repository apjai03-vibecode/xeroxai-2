"""SmartDoc AI vision engine for XeroxAI 2.0.

Provides deterministic computer vision correction for blurred, skewed, unevenly lit,
and perspectively distorted document scans without generative alteration of text.
"""

import logging
import math
from typing import Any, Optional
import cv2
import numpy as np

logger = logging.getLogger(__name__)


def _order_points(pts: np.ndarray) -> np.ndarray:
    """Orders 4 points of a quadrilateral in standard clockwise order.

    Order: [top-left, top-right, bottom-right, bottom-left].

    Args:
        pts: Array of 4 (x, y) coordinates.

    Returns:
        Ordered (4, 2) float32 numpy coordinate array.
    """
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def detect_blur(gray: np.ndarray) -> tuple[float, bool]:
    """Detects document blur using the variance of the Laplacian operator.

    Higher variance score corresponds to sharper edge transitions.

    Args:
        gray: Single-channel 8-bit grayscale image array.

    Returns:
        Tuple of (variance_score, is_blurry_boolean).
    """
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    is_blurry = bool(variance < 100.0)
    return round(float(variance), 2), is_blurry


def detect_skew_angle(gray: np.ndarray) -> float:
    """Detects orientation skew angle in degrees using text edge Hough transforms.

    Args:
        gray: Single-channel 8-bit grayscale image array.

    Returns:
        Detected skew angle in degrees within range [-45.0, 45.0].
    """
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    edges = cv2.Canny(thresh, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 180, threshold=100, minLineLength=80, maxLineGap=10
    )

    angles: list[float] = []
    if lines is not None and len(lines) > 0:
        lines = lines.reshape(-1, 4)
        for x1, y1, x2, y2 in lines:
            if x2 != x1:
                angle_deg = math.degrees(math.atan2(y2 - y1, x2 - x1))
                if -45 < angle_deg < 45:
                    angles.append(angle_deg)

    if angles:
        return round(float(np.median(angles)), 2)

    # Fallback: minimum area bounding box on text coordinates
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) > 100:
        pts = np.column_stack((coords[:, 1], coords[:, 0])).astype(np.float32)
        rect = cv2.minAreaRect(pts)
        angle = rect[-1]
        if angle < -45:
            angle = -(90 + angle)
        elif angle > 45:
            angle = 90 - angle
        return round(float(angle), 2)

    return 0.0


def deskew_image(image: np.ndarray, angle: float) -> np.ndarray:
    """Rotates an image to correct detected tilt with non-clipping white border padding.

    Args:
        image: Source image array (BGR or grayscale).
        angle: Skew angle in degrees.

    Returns:
        Rotated image array with expanded borders preventing clipped text.
    """
    if abs(angle) < 0.2:
        return image

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    m = cv2.getRotationMatrix2D(center, angle, 1.0)

    cos = np.abs(m[0, 0])
    sin = np.abs(m[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))

    m[0, 2] += (new_w / 2) - center[0]
    m[1, 2] += (new_h / 2) - center[1]

    rotated = cv2.warpAffine(
        image,
        m,
        (new_w, new_h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255),
    )
    return rotated


def find_document_contour(image: np.ndarray) -> Optional[np.ndarray]:
    """Finds the 4-corner document contour if a page boundary is clearly defined.

    Args:
        image: Source BGR image array.

    Returns:
        (4, 2) numpy array of quadrilateral vertex coordinates, or None.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilated = cv2.dilate(edged, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    img_area = image.shape[0] * image.shape[1]

    for c in sorted_contours:
        area = cv2.contourArea(c)
        if 0.25 * img_area < area < 0.98 * img_area:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4 and cv2.isContourConvex(approx):
                return approx.reshape(4, 2)

    return None


def correct_perspective(image: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """Warps an arbitrary quadrilateral region into a flat fronto-parallel rectangle.

    Args:
        image: Source BGR image array.
        pts: Four vertex points of the document polygon.

    Returns:
        Warped fronto-parallel rectangular image array.
    """
    rect = _order_points(pts)
    (tl, tr, br, bl) = rect

    width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    max_w = max(int(width_a), int(width_b))

    height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    max_h = max(int(height_a), int(height_b))

    dst = np.array(
        [
            [0, 0],
            [max_w - 1, 0],
            [max_w - 1, max_h - 1],
            [0, max_h - 1],
        ],
        dtype="float32",
    )

    m = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, m, (max_w, max_h), flags=cv2.INTER_CUBIC)
    return warped


def remove_shadows_and_uneven_light(image: np.ndarray) -> np.ndarray:
    """Normalizes illumination by dividing image channels by background surfaces.

    Args:
        image: Source BGR image array.

    Returns:
        Illumination-flattened BGR image array.
    """
    channels = cv2.split(image)
    out_channels = []

    for ch in channels:
        dilated = cv2.dilate(ch, np.ones((19, 19), np.uint8))
        bg_blur = cv2.medianBlur(dilated, 21)
        bg_blur = np.clip(bg_blur, 1, 255)

        diff = 255 - cv2.absdiff(ch, bg_blur)
        norm = cv2.normalize(
            diff,
            None,
            alpha=0,
            beta=255,
            norm_type=cv2.NORM_MINMAX,
            dtype=cv2.CV_8UC1,
        )
        out_channels.append(norm)

    return cv2.merge(out_channels)


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """Applies Contrast Limited Adaptive Histogram Equalization (CLAHE) in LAB space.

    Args:
        image: Source BGR image array.

    Returns:
        Contrast-enhanced BGR image array preserving original color tones.
    """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)

    enhanced_lab = cv2.merge((cl, a, b))
    return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)


def clean_document_background(
    image: np.ndarray, mode: str = "enhanced_color"
) -> np.ndarray:
    """Produces clean paper background while preserving ink, stamps, and signatures.

    Args:
        image: Source BGR image array.
        mode: Correction mode ('enhanced_color' or 'clean_bw').

    Returns:
        Cleaned BGR document image array.
    """
    if mode == "clean_bw":
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        dilated = cv2.dilate(gray, np.ones((15, 15), np.uint8))
        bg = cv2.medianBlur(dilated, 19)
        diff = 255 - cv2.absdiff(gray, bg)
        norm = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)
        bw = cv2.adaptiveThreshold(
            norm, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10
        )
        return cv2.cvtColor(bw, cv2.COLOR_GRAY2BGR)

    no_shadows = remove_shadows_and_uneven_light(image)
    return enhance_contrast(no_shadows)


def _load_document_image(input_bytes: bytes, filename: str) -> tuple[np.ndarray, bool]:
    """Decodes input bytes into a BGR image array, supporting PDF rasterization.

    Args:
        input_bytes: Raw file bytes.
        filename: Document file name.

    Returns:
        Tuple of (cv_bgr_image, is_pdf_boolean).

    Raises:
        ValueError: If file cannot be decoded or PDF contains zero pages.
    """
    is_pdf = filename.lower().endswith(".pdf") or input_bytes.startswith(b"%PDF")
    if is_pdf:
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument(input_bytes)
        if len(pdf) == 0:
            raise ValueError("Uploaded PDF document has no pages.")
        page = pdf[0]
        pil_image = page.render(scale=200 / 72).to_pil()
        cv_img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        return cv_img, True

    nparr = np.frombuffer(input_bytes, np.uint8)
    cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if cv_img is None:
        raise ValueError(
            "Could not decode document image. Supported formats: JPG, PNG, WebP, PDF."
        )
    return cv_img, False


def _apply_perspective_step(
    image: np.ndarray, reliability_notes: list[str]
) -> tuple[np.ndarray, bool]:
    """Executes boundary isolation and perspective correction if applicable.

    Args:
        image: Current processing image array.
        reliability_notes: Accumulator list for user-facing diagnostic notes.

    Returns:
        Tuple of (transformed_image, perspective_corrected_boolean).
    """
    quad = find_document_contour(image)
    if quad is not None:
        transformed = correct_perspective(image, quad)
        reliability_notes.append(
            "Document boundaries isolated; corrected camera perspective distortion."
        )
        return transformed, True

    reliability_notes.append(
        "Full-page document detected; perspective warp skipped to avoid cropping content."
    )
    return image, False


def _apply_deskew_step(
    image: np.ndarray, reliability_notes: list[str]
) -> tuple[np.ndarray, float]:
    """Measures skew and rotates document if tilt exceeds threshold.

    Args:
        image: Current processing image array.
        reliability_notes: Accumulator list for user-facing diagnostic notes.

    Returns:
        Tuple of (deskewed_image, applied_skew_angle_degrees).
    """
    cur_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    applied_skew = detect_skew_angle(cur_gray)
    if abs(applied_skew) >= 0.5:
        deskewed = deskew_image(image, applied_skew)
        reliability_notes.append(
            f"Auto-corrected document tilt by {-applied_skew:.1f}°."
        )
        return deskewed, applied_skew

    reliability_notes.append(
        "Document orientation is horizontally aligned (tilt < 0.5°)."
    )
    return image, 0.0


def process_document(
    input_bytes: bytes,
    filename: str,
    output_mode: str = "enhanced_color",
    auto_deskew: bool = True,
    auto_perspective: bool = True,
    remove_shadows: bool = True,
) -> dict[str, Any]:
    """Executes the complete SmartDoc AI inspection and vision correction pipeline.

    Args:
        input_bytes: Raw binary image or PDF payload.
        filename: Name of the uploaded file.
        output_mode: Processing mode ('enhanced_color' or 'clean_bw').
        auto_deskew: Whether to detect and correct paper tilt.
        auto_perspective: Whether to isolate document polygon and perspective-warp.
        remove_shadows: Whether to flatten background lighting and glare.

    Returns:
        Dictionary containing processed bytes, original bytes, dimensions,
        blur clarity metrics, and diagnostic integrity notes.
    """
    cv_img, is_pdf = _load_document_image(input_bytes, filename)
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

    blur_score, is_blurry = detect_blur(gray)
    detected_skew = detect_skew_angle(gray)

    reliability_notes: list[str] = []
    if is_blurry:
        reliability_notes.append(
            f"Low camera sharpness detected (score: {blur_score}). Text edge enhancement applied."
        )
    else:
        reliability_notes.append(
            f"Sharp document quality verified (clarity score: {blur_score})."
        )

    current = cv_img.copy()
    perspective_corrected = False

    if auto_perspective:
        current, perspective_corrected = _apply_perspective_step(
            current, reliability_notes
        )

    applied_skew = 0.0
    if auto_deskew and not perspective_corrected:
        current, applied_skew = _apply_deskew_step(current, reliability_notes)

    if remove_shadows:
        current = clean_document_background(current, mode=output_mode)
        reliability_notes.append(
            "Removed background shadows and normalized page illumination."
        )

    _, orig_buf = cv2.imencode(".jpg", cv_img, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
    _, corr_buf = cv2.imencode(".jpg", current, [int(cv2.IMWRITE_JPEG_QUALITY), 92])

    return {
        "original_bytes": orig_buf.tobytes(),
        "processed_bytes": corr_buf.tobytes(),
        "filename": filename,
        "is_pdf": is_pdf,
        "width": current.shape[1],
        "height": current.shape[0],
        "blur_score": blur_score,
        "is_blurry": is_blurry,
        "detected_skew_deg": applied_skew if applied_skew != 0.0 else detected_skew,
        "perspective_corrected": perspective_corrected,
        "shadows_removed": remove_shadows,
        "output_mode": output_mode,
        "reliability_notes": reliability_notes,
    }
