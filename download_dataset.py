"""
Download the primary dataset from Roboflow Universe in YOLOv8 format.

Primary dataset:
  Helmet and Number Plate Detection for Motorbike Safety (iityz)
  https://universe.roboflow.com/helmet-and-number-plate-detection-project/helmet-and-number-plate-detection-for-motorbike-safety-iityz

HOW TO GET THE EXACT SNIPPET:
  1. Open the dataset page above, click "Download Dataset".
  2. Choose format = YOLOv8, choose "show download code".
  3. Copy the workspace / project / version values into the placeholders below.
  4. Put your Roboflow API key in the ROBOFLOW_API_KEY env var.

Run:
  export ROBOFLOW_API_KEY=xxxx
  python download_dataset.py
"""
import os
from roboflow import Roboflow
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("ROBOFLOW_API_KEY")
if not API_KEY:
    raise SystemExit("Set ROBOFLOW_API_KEY env var first (get it from roboflow.com -> Settings).")

# --- Replace these with the exact values from the dataset's download snippet ---
WORKSPACE = "helmet-and-number-plate-detection-project"
PROJECT   = "helmet-and-number-plate-detection-for-motorbike-safety-iityz"
VERSION   = 3   # use the latest version number shown on the dataset page
# ------------------------------------------------------------------------------

rf = Roboflow(api_key=API_KEY)
project = rf.workspace(WORKSPACE).project(PROJECT)
dataset = project.version(VERSION).download("yolov8")

print(f"\nDownloaded to: {dataset.location}")
print("This folder contains a data.yaml — pass its path to train.py")
