"""
FastAPI backend for the GRiD Traffic Violation system.

Run:
  uvicorn server:app --reload --port 8000

Endpoints:
  POST /api/detect       — upload image → annotated + violations
  POST /api/detect/raw   — upload image → raw YOLO boxes (debug)
  POST /api/challan/pdf  — generate downloadable PDF challan
  POST /api/rag/query    — query MV Act sections
  POST /api/rag/chat     — conversational legal chatbot
  GET  /api/analytics    — aggregate stats
  GET  /api/history      — search violations by plate
  GET  /api/health       — health check
"""
import os
import io
import base64
import hashlib
from datetime import datetime

import cv2
import numpy as np
from PIL import Image
from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse, FileResponse
from pydantic import BaseModel

import config
from detector import ViolationDetector
from ocr import read_plate
from challan_agent import generate_challan
from pdf_gen import generate_pdf
import db

# ── App init ───────────────────────────────────────────────────────────────
app = FastAPI(title="GRiD Traffic Violation AI", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IMAGE_DIR = "images"
os.makedirs(IMAGE_DIR, exist_ok=True)


# ── Lazy model loading ────────────────────────────────────────────────────
_detector = None

def _get_detector() -> ViolationDetector:
    global _detector
    if _detector is None:
        _detector = ViolationDetector()
    return _detector

# ── Helpers ────────────────────────────────────────────────────────────────
def _read_image(file_bytes: bytes) -> np.ndarray:
    """Convert uploaded file bytes to BGR numpy array."""
    pil = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

def _img_to_base64(img_bgr: np.ndarray, quality: int = 85) -> str:
    """Encode BGR image to base64 JPEG string."""
    _, buf = cv2.imencode(".jpg", img_bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return base64.b64encode(buf).decode("utf-8")

def _image_hash(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()[:12]

# ── Request/Response models ───────────────────────────────────────────────
class ChallanPdfRequest(BaseModel):
    plate: str = ""
    violations: list[str] = []
    total_fine: int = 0
    timestamp: str = ""
    riders: int = 1
    facts: dict = {}

class RagQueryRequest(BaseModel):
    query: str

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


# ═════════════════════════════════════════════════════════════════════════
#  ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health():
    return {"status": "ok", "models": {
        "primary": config.MODEL_PATH,
        "tvd": getattr(config, "TVD_MODEL_PATH", "N/A"),
    }}


@app.post("/api/detect")
async def detect(
    file: UploadFile = File(...),
    conf: float = Query(default=0.25, ge=0.05, le=0.95),
):
    """Upload image → detect violations → return annotated image + records."""
    data = await file.read()
    img_bgr = _read_image(data)
    img_hash = _image_hash(data)

    detector = _get_detector()
    detector.conf = conf
    annotated, records = detector.detect(img_bgr, verbose=True)

    img_path = os.path.join(IMAGE_DIR, f"{img_hash}.jpg")
    cv2.imwrite(img_path, annotated)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Process each violation: OCR + challan + persist
    results = []
    for i, r in enumerate(records):
        plate_result = read_plate(img_bgr, r["plate_box"])
        challan = generate_challan(plate_result["plate"], r["violations"], ts)

        # Persist to DB
        db.log_violation(
            plate=plate_result["plate"],
            display=plate_result["display"],
            plate_fmt=plate_result["format"],
            violations=r["violations"],
            riders=r["rider_count"],
            fine=challan["total_fine"],
            engine=plate_result["engine"],
            conf=plate_result["conf"],
            image_hash=img_hash,
            timestamp=ts,
        )

        results.append({
            "vehicle_id": i + 1,
            "plate": {
                "text": plate_result["plate"],
                "display": plate_result["display"],
                "format": plate_result["format"],
                "engine": plate_result["engine"],
                "conf": plate_result["conf"],
            },
            "violations": r["violations"],
            "rider_count": r["rider_count"],
            "challan": {
                "english": challan["english"],
                "hindi": challan.get("hindi", ""),
                "total_fine": challan["total_fine"],
            },
            "facts": {
                k: {
                    "section": v.get("section", ""),
                    "title": v.get("title", ""),
                    "fine_inr": v.get("fine_inr", 0),
                    "disqualification": v.get("disqualification", ""),
                    "compoundable": v.get("compoundable", False),
                } if v else None
                for k, v in challan.get("facts", {}).items()
            },
        })

    return {
        "annotated_image": _img_to_base64(annotated),
        "original_image": _img_to_base64(img_bgr),
        "violation_count": len(records),
        "timestamp": ts,
        "results": results,
    }


@app.post("/api/detect/raw")
async def detect_raw(
    file: UploadFile = File(...),
    conf: float = Query(default=0.25, ge=0.05, le=0.95),
):
    """Upload image → return raw YOLO boxes from both models (debug)."""
    data = await file.read()
    img_bgr = _read_image(data)

    detector = _get_detector()

    # Primary model
    primary_results = detector.model(img_bgr, conf=conf, verbose=False)[0]
    primary_img = primary_results.plot()

    response = {
        "primary": {
            "image": _img_to_base64(primary_img),
            "box_count": len(primary_results.boxes),
        }
    }

    # TVD model
    tvd = getattr(detector, "tvd_model", None)
    if tvd:
        tvd_conf = getattr(detector, "tvd_conf", 0.35)
        tvd_results = tvd(img_bgr, conf=tvd_conf, verbose=False)[0]
        tvd_img = tvd_results.plot()
        response["tvd"] = {
            "image": _img_to_base64(tvd_img),
            "box_count": len(tvd_results.boxes),
        }

    return response


@app.post("/api/challan/pdf")
async def challan_pdf(req: ChallanPdfRequest):
    """Generate a downloadable PDF challan."""
    pdf_bytes = generate_pdf({
        "plate": req.plate,
        "violations": req.violations,
        "total_fine": req.total_fine,
        "timestamp": req.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "riders": req.riders,
        "facts": req.facts,
    })
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=e-challan.pdf"},
    )

@app.get("/api/image/{img_hash}")
async def get_image(img_hash: str):
    """Serve saved annotated images."""
    img_path = os.path.join(IMAGE_DIR, f"{img_hash}.jpg")
    if os.path.exists(img_path):
        return FileResponse(img_path, media_type="image/jpeg")
    return JSONResponse(status_code=404, content={"error": "Image not found"})



@app.post("/api/rag/query")
async def rag_query(req: RagQueryRequest):
    """Query the MV Act RAG for relevant legal sections."""
    try:
        from mv_act_rag import retrieve
        hits = retrieve(req.query, n_results=3)
        return {"hits": hits, "query": req.query}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "hint": "Run: python mv_act_rag.py --build"},
        )


@app.post("/api/rag/chat")
async def rag_chat(req: ChatRequest):
    """Conversational legal chatbot using RAG retrieval."""
    try:
        from mv_act_rag import retrieve

        # Extract violation keywords from the message
        message_lower = req.message.lower()
        query_key = req.message  # default: use raw message

        # Map common terms to violation keys for better retrieval
        keyword_map = {
            "helmet": "no_helmet",
            "triple": "triple_riding",
            "three rider": "triple_riding",
            "mobile": "using_mobile",
            "phone": "using_mobile",
            "wheeling": "wheeling",
            "stunt": "wheeling",
            "speed": "speeding",
            "drunk": "drunk_driving",
            "insurance": "no_insurance",
            "seat belt": "seat_belt",
            "overload": "overloading",
        }
        for keyword, viol_key in keyword_map.items():
            if keyword in message_lower:
                query_key = viol_key
                break

        hits = retrieve(query_key, n_results=3)

        # Build a structured response
        if hits:
            sections = []
            for h in hits:
                sections.append({
                    "section": h["section"],
                    "title": h["title"],
                    "fine": h["fine_inr"],
                    "disqualification": h.get("disqualification", ""),
                    "compoundable": h.get("compoundable", False),
                    "text": h["full_text"][:500],
                    "score": h["score"],
                })

            # Build a human-friendly answer
            top = hits[0]
            answer = (
                f"According to the Motor Vehicles Act 1988 (amended 2019):\n\n"
                f"**Section {top['section']} — {top['title']}**\n\n"
                f"{top['full_text'][:400]}\n\n"
                f"**Fine:** ₹{top['fine_inr']}\n"
            )
            if top.get("disqualification"):
                answer += f"**Disqualification:** {top['disqualification']}\n"
            if top.get("compoundable"):
                answer += "**Compoundable:** Yes (can be paid on the spot)\n"

            if len(hits) > 1:
                answer += f"\n\n---\n*Also relevant: Section {hits[1]['section']} — {hits[1]['title']}*"

            return {
                "answer": answer,
                "sections": sections,
                "query_used": query_key,
            }
        else:
            return {
                "answer": "I couldn't find specific provisions matching your query in the Motor Vehicles Act. Try asking about specific violations like 'helmet', 'triple riding', or 'speeding'.",
                "sections": [],
                "query_used": query_key,
            }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "hint": "Run: python mv_act_rag.py --build"},
        )


@app.get("/api/analytics")
async def analytics():
    """Return aggregate statistics for the dashboard."""
    return db.get_stats()


@app.get("/api/history")
async def history(q: str = Query(default="", description="Plate search query")):
    """Search violation history by plate number."""
    if q.strip():
        rows = db.search_by_plate(q)
    else:
        rows = db.get_all(limit=100)
    return {"results": rows, "count": len(rows)}
