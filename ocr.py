"""
Indian Number Plate OCR — PaddleOCR 3.x + EasyOCR fallback.

PaddleOCR 3.x removed use_gpu / use_angle_cls / show_log constructor args.
New API: PaddleOCR(lang="en") only, then call .ocr(img, cls=True).

Architecture:
  1. Plate crop from YOLO detection box
  2. Multi-stage preprocessing (CLAHE, Otsu, adaptive, denoise)
  3. PaddleOCR primary — runs on top-2 preprocessed variants
  4. EasyOCR fallback — if PaddleOCR confidence is low
  5. Position-aware character correction + Indian plate regex validation
  6. Returns rich dict (plate, display, format, conf, engine)

Indian plate formats:
  Standard : KA 01 AB 1234  ->  [A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}
  BH series: 23 BH 1234 AB  ->  [0-9]{2}BH[0-9]{4}[A-Z]{1,2}
  Old short : KA 01 1234     ->  [A-Z]{2}[0-9]{2}[0-9]{4}
"""

import re
import cv2
import numpy as np

# ── lazy-load readers ──────────────────────────────────────────────────────
_paddle_reader = None
_easy_reader   = None

def _get_paddle():
    global _paddle_reader
    if _paddle_reader is None:
        try:
            from paddleocr import PaddleOCR
            # PaddleOCR 3.x clean API — no use_gpu, no show_log, no use_angle_cls
            _paddle_reader = PaddleOCR(lang="en")
        except Exception as e:
            print(f"[ocr] PaddleOCR init failed: {e}. Falling back to EasyOCR.")
            _paddle_reader = "unavailable"
    return _paddle_reader if _paddle_reader != "unavailable" else None

def _get_easy():
    global _easy_reader
    if _easy_reader is None:
        import easyocr
        _easy_reader = easyocr.Reader(["en"], gpu=False)
    return _easy_reader


# ── preprocessing ──────────────────────────────────────────────────────────
def _preprocess(crop_bgr):
    h, w = crop_bgr.shape[:2]
    scale = max(1.0, 120.0 / max(h, 1))
    if scale > 1.0:
        crop_bgr = cv2.resize(crop_bgr, None, fx=scale, fy=scale,
                              interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
    v1 = clahe.apply(gray)
    _, v2 = cv2.threshold(v1, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    v3 = cv2.adaptiveThreshold(v1, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY, 15, 8)
    v4 = cv2.fastNlMeansDenoising(v1, h=15)
    return [v1, v2, v3, v4]


# ── text cleaning ──────────────────────────────────────────────────────────
def _clean_raw(text):
    return re.sub(r"[^A-Za-z0-9]", "", text).upper()


# ── Indian plate patterns ──────────────────────────────────────────────────
_PATTERNS = [
    (re.compile(r"^([A-Z]{2})(\d{2})([A-Z]{1,2})(\d{4})$"), "standard"),
    (re.compile(r"^(\d{2})(BH)(\d{4})([A-Z]{1,2})$"),        "BH_series"),
    (re.compile(r"^([A-Z]{2})(\d{2})(\d{4})$"),               "old_short"),
]

def _validate_and_fix(text):
    for cand in [text, text.replace("O","0"), text.replace("0","O")]:
        for pat, fmt in _PATTERNS:
            if pat.match(cand):
                return _apply_position_fixes(cand, fmt), fmt
    return text, "unknown"

def _apply_position_fixes(text, fmt):
    t = list(text)
    D = {"O":"0","I":"1","S":"5","B":"8","G":"6","Z":"2","T":"7"}
    L = {"0":"O","1":"I","5":"S","8":"B","6":"G"}
    if fmt == "standard" and len(t) >= 8:
        for i in [0, 1]: t[i] = L.get(t[i], t[i])
        for i in [2, 3] + list(range(len(t)-4, len(t))): t[i] = D.get(t[i], t[i])
    elif fmt == "BH_series" and len(t) >= 8:
        for i in [0,1]+list(range(4,8)): t[i] = D.get(t[i], t[i])
    elif fmt == "old_short" and len(t) >= 8:
        for i in range(2, len(t)): t[i] = D.get(t[i], t[i])
    return "".join(t)

def _format_display(plate, fmt):
    p = plate
    if fmt == "standard"  and len(p) >= 8: return f"{p[:2]} {p[2:4]} {p[4:-4]} {p[-4:]}"
    if fmt == "BH_series" and len(p) >= 8: return f"{p[:2]} {p[2:4]} {p[4:8]} {p[8:]}"
    if fmt == "old_short"  and len(p) >= 8: return f"{p[:2]} {p[2:4]} {p[4:]}"
    return p


# ── OCR engines ────────────────────────────────────────────────────────────
PADDLE_CONF_THRESHOLD = 0.55   # if paddle beats this, skip easyocr

def _run_paddle(variants):
    paddle = _get_paddle()
    if paddle is None:
        return "", 0.0
    best_text, best_conf = "", 0.0
    for img in variants[:2]:   # paddle is slower; only top-2 variants
        try:
            result = paddle.ocr(img, cls=True)
            if not result or not result[0]:
                continue
            texts, confs = [], []
            for line in result[0]:
                if line and len(line) >= 2:
                    texts.append(line[1][0])
                    confs.append(float(line[1][1]))
            if not texts:
                continue
            text = " ".join(texts)
            conf = sum(confs) / len(confs)
            if conf > best_conf:
                best_text, best_conf = text, conf
        except Exception:
            continue
    return best_text, best_conf

def _run_easy(variants):
    reader = _get_easy()
    best_text, best_conf = "", 0.0
    for img in variants:
        results = reader.readtext(img)
        if not results:
            continue
        text = " ".join(r[1] for r in results)
        conf = float(sum(r[2] for r in results) / len(results))
        if conf > best_conf:
            best_text, best_conf = text, conf
    return best_text, best_conf


# ── public API ─────────────────────────────────────────────────────────────
def read_plate(image_bgr, plate_box):
    """
    Args:
        image_bgr : full frame BGR numpy array
        plate_box : [x1, y1, x2, y2] from YOLO, or None
    Returns dict:
        plate   : cleaned plate string
        display : spaced string e.g. 'KA 01 AB 1234'
        format  : 'standard' | 'BH_series' | 'old_short' | 'unknown'
        conf    : float 0-1
        engine  : 'paddleocr' | 'easyocr' | 'none'
    """
    empty = {"plate":"","display":"NOT READABLE",
             "format":"unknown","conf":0.0,"engine":"none"}

    if plate_box is None:
        return empty

    x1, y1, x2, y2 = [max(0, int(v)) for v in plate_box]
    crop = image_bgr[y1:y2, x1:x2]
    if crop.size == 0:
        return empty

    variants = _preprocess(crop)

    # Primary: PaddleOCR
    raw, conf, engine = "", 0.0, "none"
    p_text, p_conf = _run_paddle(variants)
    if p_text:
        raw, conf, engine = p_text, p_conf, "paddleocr"

    # Fallback: EasyOCR if paddle confidence is low or paddle unavailable
    if conf < PADDLE_CONF_THRESHOLD:
        e_text, e_conf = _run_easy(variants)
        if e_conf > conf:
            raw, conf, engine = e_text, e_conf, "easyocr"

    if not raw.strip():
        return empty

    cleaned        = _clean_raw(raw)
    fixed, fmt     = _validate_and_fix(cleaned)
    display        = _format_display(fixed, fmt)
    if not (6 <= len(fixed) <= 12):
        conf = min(conf, 0.4)

    return {"plate":fixed,"display":display,
            "format":fmt,"conf":round(conf,3),"engine":engine}


# ── quick local test: python ocr.py path/to/plate.jpg ─────────────────────
if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if not path:
        print("Usage: python ocr.py path/to/plate.jpg"); sys.exit(0)
    img = cv2.imread(path)
    if img is None:
        print(f"Could not read: {path}"); sys.exit(1)
    h, w = img.shape[:2]
    r = read_plate(img, [0, 0, w, h])
    print(f"Plate   : {r['display']}")
    print(f"Format  : {r['format']}")
    print(f"Conf    : {r['conf']:.3f}")
    print(f"Engine  : {r['engine']}")