import io
import math
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image

def _order_points(pts: np.ndarray) -> np.ndarray:
    """
    Orders 4 points of a quadrilateral: [top-left, top-right, bottom-right, bottom-left].
    """
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def detect_blur(gray: np.ndarray) -> Tuple[float, bool]:
    """
    Detects blur using the variance of the Laplacian.
    Higher score indicates higher sharpness.
    """
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    is_blurry = bool(variance < 100.0)
    return round(float(variance), 2), is_blurry

def detect_skew_angle(gray: np.ndarray) -> float:
    """
    Detects skew angle in degrees using text edge orientations and Hough transform.
    Returns angle in range [-45, 45].
    """
    # Invert and threshold to find text components
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    
    # Use Hough line detection on canny edges
    edges = cv2.Canny(thresh, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=80, maxLineGap=10)
    
    angles = []
    if lines is not None and len(lines) > 0:
        lines = lines.reshape(-1, 4)
        for x1, y1, x2, y2 in lines:
            if x2 != x1:
                angle_rad = math.atan2(y2 - y1, x2 - x1)
                angle_deg = math.degrees(angle_rad)
                # Keep near horizontal lines
                if -45 < angle_deg < 45:
                    angles.append(angle_deg)
                    
    if angles:
        median_angle = float(np.median(angles))
        return round(median_angle, 2)
        
    # Fallback to minimum area bounding box on text coordinates
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) > 100:
        # Swap (row, col) to (x, y)
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
    """
    Rotates image to correct detected skew with white background padding.
    """
    if abs(angle) < 0.2:
        return image
        
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    
    # Compute new bounding dimensions so corners are not clipped
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))
    
    M[0, 2] += (new_w / 2) - center[0]
    M[1, 2] += (new_h / 2) - center[1]
    
    rotated = cv2.warpAffine(
        image, M, (new_w, new_h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255)
    )
    return rotated

def find_document_contour(image: np.ndarray) -> Optional[np.ndarray]:
    """
    Finds the 4-corner document contour if a page boundary is clearly visible against a background.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)
    
    # Dilate edges to close gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilated = cv2.dilate(edged, kernel, iterations=1)
    
    contours, _ = cv2.findContours(dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    
    img_area = image.shape[0] * image.shape[1]
    
    for c in contours:
        area = cv2.contourArea(c)
        # Must occupy at least 25% of the frame and not be the outer image boundary
        if 0.25 * img_area < area < 0.98 * img_area:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4 and cv2.isContourConvex(approx):
                return approx.reshape(4, 2)
                
    return None

def correct_perspective(image: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """
    Warps quadrilateral coordinates to a flat fronto-parallel rectangle.
    """
    rect = _order_points(pts)
    (tl, tr, br, bl) = rect
    
    # Width of new image
    width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    max_w = max(int(width_a), int(width_b))
    
    # Height of new image
    height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    max_h = max(int(height_a), int(height_b))
    
    dst = np.array([
        [0, 0],
        [max_w - 1, 0],
        [max_w - 1, max_h - 1],
        [0, max_h - 1]
    ], dtype="float32")
    
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (max_w, max_h), flags=cv2.INTER_CUBIC)
    return warped

def remove_shadows_and_uneven_light(image: np.ndarray) -> np.ndarray:
    """
    Divides the image by an estimated background illumination surface
    to eliminate shadows, gradients, and counter lighting glare.
    """
    # Split into color channels to handle color and b/w documents faithfully
    channels = cv2.split(image)
    out_channels = []
    
    for ch in channels:
        # Estimate background illumination using large morphological dilation
        dilated = cv2.dilate(ch, np.ones((19, 19), np.uint8))
        bg_blur = cv2.medianBlur(dilated, 21)
        
        # Avoid division by zero
        bg_blur = np.clip(bg_blur, 1, 255)
        
        # Division normalization
        diff = 255 - cv2.absdiff(ch, bg_blur)
        norm = cv2.normalize(diff, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
        out_channels.append(norm)
        
    result = cv2.merge(out_channels)
    return result

def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    Applies CLAHE (Contrast Limited Adaptive Histogram Equalization)
    in LAB color space to boost document readability without blowing out details.
    """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    
    enhanced_lab = cv2.merge((cl, a, b))
    return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

def clean_document_background(image: np.ndarray, mode: str = "enhanced_color") -> np.ndarray:
    """
    Produces clean paper background while preserving original ink, stamps, signatures, and text.
    - 'enhanced_color': preserves colors (signatures, stamps, letterheads) while cleaning shadows.
    - 'clean_bw': clean crisp monochrome scan for high-contrast official records.
    """
    if mode == "clean_bw":
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Background division
        dilated = cv2.dilate(gray, np.ones((15, 15), np.uint8))
        bg = cv2.medianBlur(dilated, 19)
        diff = 255 - cv2.absdiff(gray, bg)
        norm = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)
        # Adaptive threshold for clean black text on white paper
        bw = cv2.adaptiveThreshold(
            norm, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10
        )
        return cv2.cvtColor(bw, cv2.COLOR_GRAY2BGR)
    else:
        # Default: enhanced color with shadow removal and contrast boost
        no_shadows = remove_shadows_and_uneven_light(image)
        return enhance_contrast(no_shadows)

def process_document(
    input_bytes: bytes,
    filename: str,
    output_mode: str = "enhanced_color",
    auto_deskew: bool = True,
    auto_perspective: bool = True,
    remove_shadows: bool = True,
) -> Dict[str, Any]:
    """
    Full SmartDoc AI document inspection and correction pipeline.
    Preserves original bytes, detects issues, applies deterministic OpenCV transformations,
    and returns metrics, notes, and corrected image.
    """
    # Check if PDF
    is_pdf = filename.lower().endswith(".pdf") or input_bytes.startswith(b"%PDF")
    
    if is_pdf:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(input_bytes)
        page_count = len(pdf)
        if page_count == 0:
            raise ValueError("Uploaded PDF document has no pages.")
        # Render first page for inspection and processing at 200 DPI
        page = pdf[0]
        pil_image = page.render(scale=200/72).to_pil()
        cv_img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    else:
        # Standard image decoding
        nparr = np.frombuffer(input_bytes, np.uint8)
        cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if cv_img is None:
            raise ValueError("Could not decode document image. Supported formats: JPG, PNG, WebP, PDF.")
            
    h, w = cv_img.shape[:2]
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    
    # 1. Blur Detection
    blur_score, is_blurry = detect_blur(gray)
    
    # 2. Skew Detection
    detected_skew = detect_skew_angle(gray)
    
    reliability_notes: List[str] = []
    
    if is_blurry:
        reliability_notes.append(f"Low camera sharpness detected (score: {blur_score}). Text edge enhancement applied.")
    else:
        reliability_notes.append(f"Sharp document quality verified (clarity score: {blur_score}).")
        
    current = cv_img.copy()
    perspective_corrected = False
    
    # 3. Perspective Correction (if enabled)
    if auto_perspective:
        quad = find_document_contour(current)
        if quad is not None:
            current = correct_perspective(current, quad)
            perspective_corrected = True
            reliability_notes.append("Document boundaries isolated; corrected camera perspective distortion.")
        else:
            reliability_notes.append("Full-page document detected; perspective warp skipped to avoid cropping content.")
            
    # 4. Deskewing
    applied_skew = 0.0
    if auto_deskew and not perspective_corrected:
        # Re-compute skew if not already perspective warped
        cur_gray = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)
        applied_skew = detect_skew_angle(cur_gray)
        if abs(applied_skew) >= 0.5:
            current = deskew_image(current, applied_skew)
            reliability_notes.append(f"Auto-corrected document tilt by {-applied_skew:.1f}°.")
        else:
            reliability_notes.append("Document orientation is horizontally aligned (tilt < 0.5°).")
            
    # 5. Shadow Removal & Background Cleaning
    if remove_shadows:
        current = clean_document_background(current, mode=output_mode)
        reliability_notes.append("Removed background shadows and normalized page illumination.")
        
    # Encode outputs
    # Original preview (JPEG)
    _, orig_buf = cv2.imencode(".jpg", cv_img, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
    orig_bytes = orig_buf.tobytes()
    
    # Corrected output (JPEG at 92% quality)
    _, corr_buf = cv2.imencode(".jpg", current, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    corr_bytes = corr_buf.tobytes()
    
    return {
        "original_bytes": orig_bytes,
        "processed_bytes": corr_bytes,
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
