"""
Central configuration for the GRiD Traffic Violation system.
Edit class-name strings here if your trained model uses different labels
(check `model.names` after training and update CLASS_ALIASES accordingly).
"""

# ---- Model ----
MODEL_PATH = "best.pt"   # primary model (helmet/plate); falls back to yolov8n.pt
FALLBACK_MODEL = "yolov8n.pt"
CONF_THRESHOLD = 0.25    # lowered from 0.35 for better recall on varied images

# ---- TVD Model (No helmet, Triple riding, Using mobile, Wheeling) ----
TVD_MODEL_PATH = "best_tvd.pt"   # trained on TVD dataset; optional — skipped if absent
TVD_CONF_THRESHOLD = 0.35

# ---- Preprocessing ----
# CLAHE + resize improves detection on low-light / varied-quality images
PREPROCESS = True
CLAHE_CLIP = 2.0
CLAHE_GRID = (8, 8)
MAX_DIM = 1280           # resize long edge if larger (keeps YOLO efficient)

# ---- Class label matching ----
# We match by NAME (case-insensitive substring), returning the FIRST category
# whose alias is found in the class name. ORDER MATTERS: no_helmet MUST come
# before helmet, because "helmet" is a substring of "no-helmet".
# Primary model (iityz v3) classes: bike, helmet, no-helmet, number-plate
# TVD model classes: No helmet, Triple riding, Using mobile, Wheeling
CLASS_ALIASES = {
    "no_helmet": ["no-helmet", "no_helmet", "no helmet", "nohelmet",
                  "without helmet", "without-helmet", "without_helmet"],
    "helmet":    ["helmet", "with helmet", "with-helmet", "with_helmet"],
    "bike":      ["bike", "motorbike", "motorcycle", "motor-bike"],
    "plate":     ["number-plate", "number_plate", "number plate", "numberplate",
                  "plate", "licence", "license"],
    "triple_riding": ["triple riding", "triple_riding", "triple-riding",
                      "tripling"],
    "using_mobile":  ["using mobile", "using_mobile", "using-mobile",
                      "mobile phone", "phone"],
    "wheeling":      ["wheeling", "wheelie", "stunt"],
}

# ---- Triple riding ----
# A "head" = any helmet OR no-helmet box. >2 heads on one bike => triple riding.
TRIPLE_RIDING_THRESHOLD = 2

# ---- Violation -> Motor Vehicles Act reference ----
# NOTE: verify current fine amounts at build time; states revise them.
# Your Legal Aid Chatbot RAG can ground these dynamically instead of this static map.
MV_ACT = {
    "no_helmet": {
        "section": "Section 194D, Motor Vehicles Act 1988",
        "fine_inr": 1000,
        "note": "Riding without a protective helmet (BIS-compliant).",
    },
    "triple_riding": {
        "section": "Section 194C, Motor Vehicles Act 1988",
        "fine_inr": 1000,
        "note": "Carrying more than one pillion rider on a two-wheeler.",
    },
    "using_mobile": {
        "section": "Section 184, Motor Vehicles Act 1988",
        "fine_inr": 5000,
        "note": "Using a hand-held communication device while driving.",
    },
    "wheeling": {
        "section": "Section 184, Motor Vehicles Act 1988",
        "fine_inr": 5000,
        "note": "Dangerous driving / stunts — wheeling on a public road.",
    },
}