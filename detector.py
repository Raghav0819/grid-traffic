"""
Detection + violation logic — dual-model architecture.

Model 1 (primary): bike, helmet, no-helmet, number-plate
Model 2 (TVD):     Triple riding, No helmet, Using mobile  (optional)

Loads both YOLO models, runs inference, then applies rule-based logic:
  - NO HELMET   : primary model's 'no_helmet' class OR TVD's 'No helmet'
  - TRIPLE RIDING: TVD direct detection OR head-count > threshold (fallback)
  - USING MOBILE : TVD direct detection

A "head" = any helmet OR no-helmet detection. We use head-count as a proxy for
rider-count because the primary dataset has no separate 'person' class.
"""
import os
import cv2
import numpy as np
from ultralytics import YOLO

import config


# ----------------------------- preprocessing --------------------------------
def preprocess(img_bgr):
    """Apply CLAHE (contrast enhancement) + resize if image is too large.
    This significantly helps on images with different lighting/resolution
    than the training set."""
    h, w = img_bgr.shape[:2]

    # Resize if too large (keeps aspect ratio)
    max_dim = getattr(config, "MAX_DIM", 1280)
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img_bgr = cv2.resize(img_bgr, None, fx=scale, fy=scale,
                             interpolation=cv2.INTER_AREA)

    # CLAHE on the L channel of LAB color space (enhances contrast without
    # distorting colors — helps with low-light and over-exposed images)
    clip = getattr(config, "CLAHE_CLIP", 2.0)
    grid = getattr(config, "CLAHE_GRID", (8, 8))
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=grid)
    l = clahe.apply(l)
    img_bgr = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)

    return img_bgr


# ----------------------------- geometry helpers -----------------------------
def _center(b):
    x1, y1, x2, y2 = b
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def _point_in_box(pt, box, margin=0.0):
    x, y = pt
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    return (x1 - margin * w) <= x <= (x2 + margin * w) and \
           (y1 - margin * h) <= y <= (y2 + margin * h)


def _iou(boxA, boxB):
    """Intersection-over-union between two [x1,y1,x2,y2] boxes."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    inter = max(0, xB - xA) * max(0, yB - yA)
    areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    areaB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    union = areaA + areaB - inter
    return inter / union if union > 0 else 0.0


def _expand_box(box, up=1.0, side=0.3, down=0.1):
    """Expand a bike box: primarily upward (riders sit above the bike body),
    slightly sideways (handles off-center angles), and a bit downward."""
    x1, y1, x2, y2 = box
    h = y2 - y1
    w = x2 - x1
    return [x1 - side * w, y1 - up * h, x2 + side * w, y2 + down * h]


def _dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


# ----------------------------- class matching -----------------------------
def _category_of(name):
    n = name.lower().strip()
    for cat, aliases in config.CLASS_ALIASES.items():
        if any(a in n for a in aliases):
            return cat
    return None


# ----------------------------- main detector -----------------------------
class ViolationDetector:
    def __init__(self, model_path=None, conf=None):
        # --- Primary model (helmet / plate / bike) ---
        path = model_path or config.MODEL_PATH
        if not os.path.exists(path):
            print(f"[detector] {path} not found, falling back to {config.FALLBACK_MODEL} "
                  f"(violation classes will be limited until you train).")
            path = config.FALLBACK_MODEL
        self.model = YOLO(path)
        self.conf = conf if conf is not None else config.CONF_THRESHOLD
        print(f"[detector] Primary model loaded: {path}  (classes: {self.model.names})")

        # --- TVD model (triple riding / using mobile) — optional ---
        tvd_path = getattr(config, "TVD_MODEL_PATH", "best_tvd.pt")
        if os.path.exists(tvd_path):
            self.tvd_model = YOLO(tvd_path)
            self.tvd_conf = getattr(config, "TVD_CONF_THRESHOLD", 0.35)
            print(f"[detector] TVD model loaded: {tvd_path}  (classes: {self.tvd_model.names})")
        else:
            self.tvd_model = None
            print(f"[detector] TVD model not found at {tvd_path} — "
                  f"triple riding uses head-count fallback only.")

    def _run_primary(self, processed):
        """Run primary model → categorize detections."""
        results = self.model(processed, conf=self.conf, verbose=False)[0]
        names = results.names

        bikes, heads, plates = [], [], []
        all_dets = []
        for box, cls, score in zip(results.boxes.xyxy.cpu().numpy(),
                                   results.boxes.cls.cpu().numpy(),
                                   results.boxes.conf.cpu().numpy()):
            cat = _category_of(names[int(cls)])
            b = [float(v) for v in box]
            rec = {"box": b, "conf": float(score)}
            all_dets.append((names[int(cls)], cat, float(score), b, "primary"))

            if cat == "bike":
                bikes.append(rec)
            elif cat == "helmet":
                heads.append({**rec, "helmeted": True})
            elif cat == "no_helmet":
                heads.append({**rec, "helmeted": False})
            elif cat == "plate":
                plates.append(rec)

        return bikes, heads, plates, all_dets

    def _run_tvd(self, processed):
        """Run TVD model → extract direct violation detections."""
        if not self.tvd_model:
            return [], [], []

        results = self.tvd_model(processed, conf=self.tvd_conf, verbose=False)[0]
        names = results.names

        tvd_violations = []   # direct triple_riding / using_mobile / wheeling boxes
        tvd_no_helmets = []   # no-helmet from TVD (merged with primary)
        all_dets = []
        for box, cls, score in zip(results.boxes.xyxy.cpu().numpy(),
                                   results.boxes.cls.cpu().numpy(),
                                   results.boxes.conf.cpu().numpy()):
            cat = _category_of(names[int(cls)])
            b = [float(v) for v in box]
            rec = {"box": b, "conf": float(score), "violation": cat}
            all_dets.append((names[int(cls)], cat, float(score), b, "tvd"))

            if cat == "triple_riding":
                tvd_violations.append(rec)
            elif cat == "using_mobile":
                tvd_violations.append(rec)
            elif cat == "wheeling":
                tvd_violations.append(rec)
            elif cat == "no_helmet":
                tvd_no_helmets.append(rec)

        return tvd_violations, tvd_no_helmets, all_dets

    def detect(self, image_bgr, verbose=True):
        """Returns (annotated_image_bgr, violation_records).

        If verbose=True, prints detection details to console for debugging.
        """
        # --- Preprocessing ---
        if getattr(config, "PREPROCESS", False):
            processed = preprocess(image_bgr.copy())
        else:
            processed = image_bgr

        # --- Run both models ---
        bikes, heads, plates, primary_dets = self._run_primary(processed)
        tvd_violations, tvd_no_helmets, tvd_dets = self._run_tvd(processed)

        # Merge TVD no-helmet detections into heads list (deduplicated)
        for tvd_nh in tvd_no_helmets:
            # Check if primary already detected a similar no-helmet box (IoU > 0.3)
            duplicate = any(_iou(tvd_nh["box"], h["box"]) > 0.3
                           for h in heads if not h["helmeted"])
            if not duplicate:
                heads.append({"box": tvd_nh["box"], "conf": tvd_nh["conf"],
                              "helmeted": False})

        all_dets = primary_dets + tvd_dets
        if verbose:
            print(f"\n[detector] Raw detections: {len(all_dets)}"
                  f"  (primary: {len(primary_dets)}, tvd: {len(tvd_dets)})")
            for name, cat, score, b, src in all_dets:
                print(f"  [{src:7s}] {name:<16} → {cat or '?':<14} conf={score:.3f}  "
                      f"box=[{int(b[0])},{int(b[1])},{int(b[2])},{int(b[3])}]")
            no_helmet_count = sum(1 for h in heads if not h["helmeted"])
            print(f"  Bikes: {len(bikes)}, Heads: {len(heads)} "
                  f"(no-helmet: {no_helmet_count}), Plates: {len(plates)}, "
                  f"TVD violations: {len(tvd_violations)}")

        records = []

        # ===== 1. Direct TVD violations (triple_riding, using_mobile) =====
        # These are full-frame detections — they stand on their own.
        tvd_used_boxes = set()
        for tv in tvd_violations:
            vtype = tv["violation"]  # "triple_riding" or "using_mobile"

            # Find nearest plate
            tc = _center(tv["box"])
            plate = min(plates, key=lambda p: _dist(_center(p["box"]), tc)) \
                if plates else None

            # Determine rider count for display (if triple_riding, at least 3)
            rider_count = 3 if vtype == "triple_riding" else 1

            # Check if any no-helmet heads overlap this TVD box → compound violation
            violations = [vtype]
            for h in heads:
                if not h["helmeted"] and _iou(h["box"], tv["box"]) > 0.05:
                    if "no_helmet" not in violations:
                        violations.append("no_helmet")

            records.append({
                "bike_box": tv["box"],
                "rider_count": rider_count,
                "violations": violations,
                "plate_box": plate["box"] if plate else None,
            })
            tvd_used_boxes.add(tuple(tv["box"]))

        # ===== 2. Primary model bike-based violations (existing logic) =====
        for bike in bikes:
            # Skip if a TVD detection already covers this bike area
            bike_covered = any(_iou(bike["box"], list(tb)) > 0.3
                              for tb in tvd_used_boxes)
            if bike_covered:
                continue

            region = _expand_box(bike["box"], up=1.5, side=0.3, down=0.1)

            # Associate heads with this bike
            assoc = [h for h in heads
                     if _point_in_box(_center(h["box"]), region, margin=0.2)]
            if not assoc:
                for h in heads:
                    if _iou(h["box"], region) > 0.05:
                        assoc.append(h)

            rider_count = len(assoc)
            no_helmet_here = any(not h["helmeted"] for h in assoc)

            if verbose:
                print(f"  Bike [{int(bike['box'][0])},{int(bike['box'][1])},"
                      f"{int(bike['box'][2])},{int(bike['box'][3])}] "
                      f"→ riders={rider_count}, no_helmet={no_helmet_here}")

            violations = []
            if no_helmet_here:
                violations.append("no_helmet")
            if rider_count > config.TRIPLE_RIDING_THRESHOLD:
                violations.append("triple_riding")

            if not violations:
                continue

            # Associate nearest plate
            bc = _center(bike["box"])
            bw = bike["box"][2] - bike["box"][0]
            cand = [p for p in plates
                    if bike["box"][0] - 0.3 * bw
                    <= _center(p["box"])[0]
                    <= bike["box"][2] + 0.3 * bw]
            plate = min(cand, key=lambda p: _dist(_center(p["box"]), bc)) if cand else None

            records.append({
                "bike_box": bike["box"],
                "rider_count": rider_count,
                "violations": violations,
                "plate_box": plate["box"] if plate else None,
            })

        # ===== 3. Orphaned no-helmet fallback (no bike detected) =====
        associated_heads = set()
        for bike in bikes:
            region = _expand_box(bike["box"], up=1.5, side=0.3, down=0.1)
            for i, h in enumerate(heads):
                if _point_in_box(_center(h["box"]), region, margin=0.2):
                    associated_heads.add(i)
                elif _iou(h["box"], region) > 0.05:
                    associated_heads.add(i)
        # Also mark heads used by TVD violations
        for i, h in enumerate(heads):
            for tb in tvd_used_boxes:
                if _iou(h["box"], list(tb)) > 0.05:
                    associated_heads.add(i)

        orphaned_nh = [h for i, h in enumerate(heads)
                       if not h["helmeted"] and i not in associated_heads]

        if orphaned_nh:
            if verbose:
                print(f"  ⚠️  {len(orphaned_nh)} orphaned no-helmet → fallback violations")
            for nh in orphaned_nh:
                nc = _center(nh["box"])
                
                # Find a plate that is BELOW the head and horizontally aligned
                valid_plates = []
                for p in plates:
                    pc = _center(p["box"])
                    # Plate must be below the head (y is larger)
                    if pc[1] > nc[1]:
                        # Horizontal distance shouldn't be massive
                        hw = nh["box"][2] - nh["box"][0]
                        if abs(pc[0] - nc[0]) < hw * 4.0:
                            valid_plates.append(p)
                            
                # Prioritize plates that are directly underneath the rider (horizontal alignment)
                # rather than Euclidean distance, because plates can be mounted very low.
                plate = min(valid_plates, key=lambda p: abs(_center(p["box"])[0] - nc[0])) \
                    if valid_plates else None
                    
                records.append({
                    "bike_box": nh["box"],
                    "rider_count": 1,
                    "violations": ["no_helmet"],
                    "plate_box": plate["box"] if plate else None,
                })

        if verbose:
            print(f"  → Total violations: {len(records)}\n")

        # Annotate on the ORIGINAL image (not preprocessed), for display
        annotated = self._annotate(image_bgr.copy(), records)
        return annotated, records

    # ----------------------------- drawing -----------------------------
    @staticmethod
    def _annotate(img, records):
        # Color per violation type
        COLORS = {
            "no_helmet": (0, 0, 255),        # red
            "triple_riding": (0, 140, 255),   # orange
            "using_mobile": (255, 0, 255),    # magenta
            "wheeling": (0, 255, 255),        # yellow/cyan
        }
        YELLOW = (0, 215, 255)

        for i, r in enumerate(records, 1):
            # Pick color based on first violation
            primary_v = r["violations"][0] if r["violations"] else "no_helmet"
            color = COLORS.get(primary_v, (0, 0, 255))

            x1, y1, x2, y2 = [int(v) for v in r["bike_box"]]
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

            label = f"V{i}: " + " + ".join(v.replace("_", " ").upper() for v in r["violations"])
            label += f"  (riders:{r['rider_count']})"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
            cv2.rectangle(img, (x1, y1 - th - 8), (x1 + tw + 6, y1), color, -1)
            cv2.putText(img, label, (x1 + 3, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

            if r["plate_box"]:
                px1, py1, px2, py2 = [int(v) for v in r["plate_box"]]
                cv2.rectangle(img, (px1, py1), (px2, py2), YELLOW, 2)
        return img


# ---- Quick test: python detector.py test_image.jpg ----
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python detector.py <image_path>")
        sys.exit(1)
    img = cv2.imread(sys.argv[1])
    if img is None:
        print(f"Cannot read: {sys.argv[1]}")
        sys.exit(1)
    det = ViolationDetector()
    annotated, records = det.detect(img, verbose=True)
    out = sys.argv[1].rsplit(".", 1)[0] + "_result.jpg"
    cv2.imwrite(out, annotated)
    print(f"Saved → {out}")
