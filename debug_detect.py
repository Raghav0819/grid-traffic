"""
Debug script — shows ALL raw YOLO detections (before violation logic).
Run:  python debug_detect.py <image_path> [--conf 0.15]

This helps answer: is the model not detecting at all, or is the
association/violation logic discarding valid detections?
"""
import argparse
import cv2
from ultralytics import YOLO
import config


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image", help="path to test image")
    ap.add_argument("--conf", type=float, default=0.15,
                    help="confidence threshold (lower = more detections)")
    ap.add_argument("--model", default=config.MODEL_PATH)
    args = ap.parse_args()

    model = YOLO(args.model)
    img = cv2.imread(args.image)
    if img is None:
        raise SystemExit(f"Cannot read image: {args.image}")

    print(f"\n{'='*60}")
    print(f"Model : {args.model}")
    print(f"Classes: {model.names}")
    print(f"Image : {args.image}  ({img.shape[1]}x{img.shape[0]})")
    print(f"Conf  : {args.conf}")
    print(f"{'='*60}\n")

    results = model(img, conf=args.conf, verbose=False)[0]

    if len(results.boxes) == 0:
        print("⚠️  ZERO detections at this confidence. The model sees nothing.")
        print("    → This means the domain gap is the problem, not the logic.")
        print("    → Try a traffic-surveillance-style image from your dataset.\n")
        # Show at even lower conf
        results_low = model(img, conf=0.05, verbose=False)[0]
        if len(results_low.boxes) > 0:
            print(f"  At conf=0.05 the model finds {len(results_low.boxes)} boxes:")
            for box, cls, score in zip(results_low.boxes.xyxy.cpu().numpy(),
                                       results_low.boxes.cls.cpu().numpy(),
                                       results_low.boxes.conf.cpu().numpy()):
                name = model.names[int(cls)]
                print(f"    {name:15s}  conf={score:.3f}  box={[int(v) for v in box]}")
        return

    print(f"Total raw detections: {len(results.boxes)}\n")
    print(f"{'Class':<18} {'Conf':>6}  {'Box (x1 y1 x2 y2)'}")
    print("-" * 60)
    for box, cls, score in zip(results.boxes.xyxy.cpu().numpy(),
                               results.boxes.cls.cpu().numpy(),
                               results.boxes.conf.cpu().numpy()):
        name = model.names[int(cls)]
        coords = [int(v) for v in box]
        print(f"  {name:<16} {score:>6.3f}  {coords}")

    # Draw ALL boxes on the image
    annotated = results.plot()
    out_path = args.image.rsplit(".", 1)[0] + "_debug.jpg"
    cv2.imwrite(out_path, annotated)
    print(f"\nAnnotated debug image saved → {out_path}")

    # Also run a quick association sanity check
    print(f"\n{'='*60}")
    print("ASSOCIATION CHECK (same logic as detector.py)")
    print(f"{'='*60}")
    from detector import ViolationDetector, _category_of, _center, _point_in_box, _expand_box

    bikes, heads = [], []
    for box, cls, score in zip(results.boxes.xyxy.cpu().numpy(),
                               results.boxes.cls.cpu().numpy(),
                               results.boxes.conf.cpu().numpy()):
        cat = _category_of(model.names[int(cls)])
        b = [float(v) for v in box]
        if cat == "bike":
            bikes.append(b)
        elif cat in ("helmet", "no_helmet"):
            heads.append({"box": b, "cat": cat})

    print(f"Bikes found : {len(bikes)}")
    print(f"Heads found : {len(heads)}  (helmet + no_helmet)")

    for i, bike in enumerate(bikes):
        region = _expand_box(bike, up=1.5, side=0.3, down=0.1)
        assoc = [h for h in heads
                 if _point_in_box(_center(h["box"]), region, margin=0.15)]
        print(f"\n  Bike {i}: box={[int(v) for v in bike]}")
        print(f"    Expanded search region: {[int(v) for v in region]}")
        print(f"    Associated heads: {len(assoc)}")
        for h in assoc:
            print(f"      → {h['cat']}  box={[int(v) for v in h['box']]}")
        if not assoc:
            print(f"    ⚠️  No heads in region — violation logic will SKIP this bike")
            # Check if any head is close but outside the region
            for h in heads:
                cx, cy = _center(h["box"])
                print(f"    (unmatched head: {h['cat']}  center=({int(cx)},{int(cy)}))")


if __name__ == "__main__":
    main()
