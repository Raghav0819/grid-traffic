"""
Fine-tune YOLOv8 on the downloaded dataset.

Run:
  python train.py --data path/to/dataset/data.yaml --epochs 50 --model yolov8s.pt

Tips for a 5-day clock:
  - Start with yolov8n.pt (fastest) to confirm the pipeline, then yolov8s.pt for the final run.
  - On CPU this is slow; use Google Colab (free GPU) for the actual training run,
    then download best.pt and point MODEL_PATH in config.py at it.
  - After training, metrics (P, R, mAP) print automatically and are saved under runs/detect/.
"""
import argparse
from ultralytics import YOLO


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="path to data.yaml")
    ap.add_argument("--model", default="yolov8s.pt")
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=16)
    args = ap.parse_args()

    model = YOLO(args.model)
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        patience=15,           # early stop if no improvement
        plots=True,            # saves P/R curves + confusion matrix for the deck
    )

    # Validation metrics — copy these numbers into your presentation
    metrics = model.val()
    print("\n=== VALIDATION METRICS (use these in the deck) ===")
    print(f"mAP@0.5      : {metrics.box.map50:.4f}")
    print(f"mAP@0.5:0.95 : {metrics.box.map:.4f}")
    print(f"Precision    : {metrics.box.mp:.4f}")
    print(f"Recall       : {metrics.box.mr:.4f}")
    print("Best weights : runs/detect/train/weights/best.pt")


if __name__ == "__main__":
    main()
