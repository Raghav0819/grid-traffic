"""
Download the TVD (Traffic Violation Detection) dataset from Roboflow Universe
in YOLOv8 format.

Dataset: TVD — Traffic Violation Detection
  https://universe.roboflow.com/traffic-violation-detection/tvd-kp9qw
  Classes: No helmet, Triple riding, Using mobile

Run:
  python download_tvd.py
  (Requires ROBOFLOW_API_KEY in .env or environment)
"""
import os
from roboflow import Roboflow
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("ROBOFLOW_API_KEY")
if not API_KEY:
    raise SystemExit("Set ROBOFLOW_API_KEY env var first (get it from roboflow.com -> Settings).")

# --- TVD dataset identifiers ---
WORKSPACE = "traffic-violation-detection"
PROJECT   = "tvd-kp9qw"
VERSION   = 11  # version 11 per Roboflow download snippet

rf = Roboflow(api_key=API_KEY)
project = rf.workspace(WORKSPACE).project(PROJECT)
dataset = project.version(VERSION).download("yolov8")

print(f"\nDownloaded to: {dataset.location}")
print("This folder contains a data.yaml — use it to train the TVD model:")
print(f"  python train.py --data {dataset.location}/data.yaml --model yolov8s.pt --epochs 50")
print("\nAfter training, copy best.pt → best_tvd.pt in the project root.")
