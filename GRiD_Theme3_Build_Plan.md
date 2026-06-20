# Flipkart GRiD — Theme 3 Build Plan
### Agentic Traffic Violation Detection & E-Challan System (Bangalore)

---

## 1. Problem Statement

Bangalore's traffic surveillance cameras generate massive volumes of images every day. Manual inspection of this footage to catch traffic violations is labor-intensive, slow, inconsistent, and impossible to scale. As a result, the vast majority of violations — especially high-risk two-wheeler offences like riding without a helmet and triple riding — go undetected and unpenalized, directly contributing to road fatalities.

There is no automated system that can look at a traffic image, decide whether a violation occurred, identify the offending vehicle, and produce legally-usable evidence for enforcement.

**Core question:** How can a computer vision system automatically detect traffic violations from photographic evidence, identify the offending vehicle, and generate ready-to-issue legal enforcement records — accurately, at scale, and across varying conditions?

---

## 2. Solution

An end-to-end **Agentic Traffic Violation Detection & E-Challan System** that turns a raw traffic image into an enforcement-ready challan.

Pipeline in one line:
> **Image → Detect riders/vehicles → Flag violations → Read number plate → LLM agent writes the legal e-challan (bilingual, with MV Act section) → Store evidence + analytics dashboard.**

What makes it different from a typical CV submission:
- Most teams stop at "violation detected."
- **We close the full loop to enforcement** — an agentic layer auto-generates the legal challan, grounding every citation in a purpose-built **Motor Vehicles Act RAG** so the exact section, fine amount, and provision are retrieved from the actual law (not hardcoded or hallucinated), output in **English + Hindi**.
- This connects **detection → identification → law (RAG) → analytics**, which is the complete workflow the brief actually asks for (evidence generation + analytics + reporting), not just the detection slice.

**Scope (deliberately deep, not wide):** focus on the highest-density, best-data Bangalore violations:
1. No-helmet detection
2. Triple riding detection
3. License plate detection + OCR
4. MV Act RAG + agentic e-challan generation + analytics

This is a coherent, complete story — far stronger than 7 violations done shallowly. It also showcases **two AI skill axes** (computer vision + retrieval-augmented generation), which is rare in a hackathon submission and hard for other teams to match.

---

## 3. Objective

Build a scalable, demoable prototype that:
1. Automatically processes traffic images and detects riders, motorcycles, and helmets.
2. Identifies and classifies violations (no-helmet, triple riding) with confidence scores.
3. Detects and reads the offending vehicle's number plate via OCR.
4. Generates annotated evidence images + a bilingual legal e-challan citing the correct MV Act section.
5. Stores violation metadata (timestamp, plate, type) and surfaces analytics/trends through a searchable dashboard.
6. Is evaluated on **Precision, Recall, F1, and mAP** (the brief grades on these explicitly).

---

## 4. Full Implementation Plan (5 days, ~6–7 hrs/day)

### Architecture (data flow)
```
                ┌──────────────────────────────────────────────┐
                │              INPUT (image / frame)            │
                └──────────────────────┬───────────────────────┘
                                       ▼
                ┌──────────────────────────────────────────────┐
   STAGE 1      │  Preprocessing: resize, denoise, low-light    │
                │  normalization (CLAHE), handle blur/shadows   │
                └──────────────────────┬───────────────────────┘
                                       ▼
                ┌──────────────────────────────────────────────┐
   STAGE 2      │  YOLO Detection: motorcycle, rider/person,    │
                │  helmet, no-helmet, number-plate              │
                └──────────────────────┬───────────────────────┘
                                       ▼
                ┌──────────────────────────────────────────────┐
   STAGE 3      │  Violation Logic:                             │
                │  • no-helmet  → if rider has no helmet box    │
                │  • triple riding → riders-per-bike > 2        │
                │  • assign confidence scores                   │
                └──────────────────────┬───────────────────────┘
                                       ▼
                ┌──────────────────────────────────────────────┐
   STAGE 4      │  Plate crop → OCR (EasyOCR/PaddleOCR)         │
                │  → registration string                        │
                └──────────────────────┬───────────────────────┘
                                       ▼
                ┌──────────────────────────────────────────────┐
   STAGE 5      │  MV Act RAG: retrieve matching section/fine   │
                │  from vector store  →  AGENT (LLM) writes      │
                │  bilingual e-challan grounded in retrieved law │
                └──────────────────────┬───────────────────────┘
                                       ▼
                ┌──────────────────────────────────────────────┐
   STAGE 6      │  Store metadata + annotated image →           │
                │  Analytics dashboard (counts, trends, search) │
                └──────────────────────────────────────────────┘
```

### Datasets (no dataset was provided — you source these)

**Primary — use this as your base:**
**Helmet and Number Plate Detection for Motorbike Safety** (Roboflow Universe)
`universe.roboflow.com/helmet-and-number-plate-detection-project/helmet-and-number-plate-detection-for-motorbike-safety-iityz`
- Classes: **Bike, Helmet, No Helmet, Number Plate** — covers 3 of your 4 needs in one download.
- ~20,000 images, trained reference on YOLOv11/300 epochs → strong base for fine-tuning.
- Public, road-safety/enforcement focused. Download in YOLOv8 format via API key.

**Add triple riding (the one class the primary set lacks):**
**TVD — Traffic Violation Detection** (Roboflow Universe)
`universe.roboflow.com/traffic-violation-detection/tvd-kp9qw`
- Classes: **No helmet, Triple riding, Using mobile** — gives the triple-riding label, plus a bonus violation if time allows.

**Backups (optional):**
- **Indian Car Bike Number Plate** (`universe.roboflow.com/indiannumberplatesdetection/indian-car-bike-number-plate`) — ~102 Indian-plate images, useful for tuning the plate crop before OCR.
- **Motorcycle Helmet and License plate detection** (`universe.roboflow.com/object-detection-helmetslicense/motorcycle-helmet-and-license-plate-detection`) — ~1,476 images, lighter fallback if the 20k set is too heavy to train in time.

**Strategy — avoid the multi-dataset merge trap:**
1. Fine-tune ONLY on the primary (iityz) set → instantly get bike + helmet + no-helmet + plate.
2. Handle **triple riding by logic** (count riders associated with one motorcycle; if > 2, flag it) — no extra training. Keep TVD as a model-based backup.
3. Use the Indian-plate set only if EasyOCR struggles on Indian formats.
*One training run for the core. Eyeball 20–30 samples first (community label quality varies), and keep a few real Bangalore images aside for the demo to show it generalizes.*

### Day-by-day

**Day 1 — Foundation & detection baseline**
- Set up environment (Python venv, Ultralytics, OpenCV, EasyOCR).
- Pull the **primary dataset** (Helmet and Number Plate Detection for Motorbike Safety, iityz) in YOLOv8 format via API key — see the Datasets section above.
- Run YOLOv8 inference on sample images. **Goal: bounding boxes render on a test image.**
- Write the preprocessing function (resize, CLAHE for low light).

**Day 2 — Train + violation logic + metrics**
- Fine-tune YOLOv8 on the dataset (start `yolov8n` or `yolov8s` for speed; 30–50 epochs).
- Implement violation logic: associate riders/helmets with each motorcycle; flag no-helmet and triple riding (riders per bike > 2).
- Compute and record **Precision, Recall, F1, mAP@0.5** from the validation set — you'll need these numbers in the deck.

**Day 3 — Plate detection + OCR**
- Add number-plate detection (separate class or a second small model).
- Crop the plate region, run **EasyOCR / PaddleOCR**, clean the output (regex for Indian plate format `KA 01 AB 1234`).
- Handle OCR failures gracefully (low confidence → flag "manual review").

**Day 4 — MV Act RAG + agentic e-challan + evidence + analytics (your differentiator)**
- **Build the Motor Vehicles Act RAG from scratch (project-specific):**
  - *Ingest:* download the Motor Vehicles Act 1988 (with 2019 amendments) text — official source: indiacode.nic.in. Focus on Chapter XIII "Offences, Penalties and Procedure" (Sections 177–210), which holds the penalty provisions.
  - *Chunk:* split section-wise (one chunk per section/sub-section) — legal text retrieves best when chunked on its natural section boundaries, not fixed token windows.
  - *Embed:* `sentence-transformers` (e.g. `all-MiniLM-L6-v2`, or a multilingual model if you want Hindi queries too).
  - *Store:* **ChromaDB** (or FAISS) vector store, persisted locally.
  - *Retrieve:* given a detected violation (e.g. "no helmet"), query the store → return the matching section text, number, and fine.
- **Grounded challan agent:** pass the retrieved section(s) + `{violation, plate, timestamp}` to the LLM (Gemini Flash / Groq) → it writes the bilingual (EN/HI) e-challan using ONLY the retrieved provisions. Legal facts come from RAG, the LLM only formats — so no hallucinated sections.
- Save annotated evidence image (boxes + labels) and write metadata to SQLite/JSON.
- Build a simple analytics view: violation counts by type, trend over time, searchable records.

> **De-risk tip:** the RAG is completely independent of the CV pipeline (it only needs the violation *label* as a query string). Since retrieval is your strong suit, knock it out early — even Day 1 evening or in parallel — so Day 4 is just wiring, not building. Keep a tiny static section→fine map as an offline fallback so the demo never breaks if retrieval misfires.

**Day 5 — UI, polish, submission**
- Wrap everything in **Streamlit** — single `app.py`, upload image → annotated result + challan + analytics tab. Fastest path to a demo; no separate frontend to build.
- Polish the demo on 8–10 curated sample images that show clean wins.
- Prepare the **concept note / deck**: problem → solution → architecture diagram → data strategy → metrics → scalability → future scope.
- **Record a backup demo video** in case the live demo fails.

### MV Act reference cheat-sheet (also your RAG fallback map)
- No helmet → **Sec 194D**, ₹1,000 (+ possible 3-month licence disqualification)
- Triple riding / overloading two-wheeler → **Sec 194C**, ₹1,000
(These are the ground-truth answers your RAG should return — use them to sanity-check retrieval, and as the static offline fallback. Verify current amounts when you build; states revise them.)

---

## 5. Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Detection | **YOLOv8 / YOLOv11 (Ultralytics)** | Fast, accurate, huge ecosystem, easy fine-tune |
| Preprocessing | **OpenCV** (CLAHE, resize, denoise) | Handles low light / blur from the brief |
| OCR | **EasyOCR** (primary) / PaddleOCR | Better on Indian plates than Tesseract |
| Dataset source | **Roboflow Universe** — primary: Helmet+Number Plate (iityz, ~20k imgs); triple riding: TVD | Pre-labeled, YOLO-format, API download |
| Agent / LLM | **Gemini 2.0 Flash or Groq** | You already use these; fast + cheap |
| Legal grounding | **MV Act RAG built from scratch** (this project only) | Grounds challan citations in the actual law; showcases RAG skill |
| — RAG: source | **Motor Vehicles Act 1988 + 2019 amendments** (indiacode.nic.in), Ch. XIII Sec 177–210 | The penalty provisions you retrieve from |
| — RAG: embed/store | **sentence-transformers + ChromaDB** (section-wise chunks) | Lightweight, fast to stand up, retrieves on natural section boundaries |
| Storage | **SQLite + JSON** | Lightweight, demo-friendly |
| Demo / Frontend | **Streamlit** (single `app.py`, Detect + Analytics tabs) | Fastest path to a working demo; upload image → annotated result + bilingual challan |
| Metrics | Ultralytics built-in (P, R, mAP) + sklearn (F1) | Required by the brief |

---

## 6. Work Environment (notebook vs script)

Use **both**, split by job — not one or the other.

**`.ipynb` notebook — for training ONLY, on Google Colab**
- Train on Colab, not your laptop: free GPU turns YOLO training from hours (CPU) into minutes.
- The train → check metrics → inspect P/R curves → retrain loop is exactly what notebooks are for.
- Notebook cells: download dataset (Roboflow API key) → train → validate/metrics → download `best.pt`.
- Then drop `best.pt` into the local project and point `MODEL_PATH` in `config.py` at it.

**`.py` scripts — for the whole app + pipeline (everything else)**
- Hard requirement, not preference: Streamlit only runs from a script (`streamlit run app.py`), and `app.py` must import `detector.py` / `ocr.py` / `challan_agent.py` as modules. You cannot build the demo out of notebooks.
- Build locally in **VS Code**. The scaffold is already all `.py` — correct as-is.

**Setup summary**
| Where | Tool | What lives here |
|---|---|---|
| Local machine | VS Code | All `.py` files — app, detector, ocr, challan, config. Build + run the demo here. |
| Browser | Google Colab | One training notebook. Train on GPU, export `best.pt`. |

**Trap to avoid:** don't build the pipeline *logic* in a notebook because iteration feels quicker — you'll be forced to refactor it into modules on Day 5 under pressure, and notebook hidden-state bugs will bite. Write the pipeline as `.py` from the start; for fast iteration, add an `if __name__ == "__main__":` block to `detector.py` that runs on one test image, so `python detector.py` tests it without launching Streamlit.

---

## 7. Where to Start (literally your first 3 hours)

1. **Create the project + environment**
   ```bash
   mkdir grid-traffic && cd grid-traffic
   python -m venv venv && source venv/bin/activate   # (Windows: venv\Scripts\activate)
   pip install ultralytics opencv-python easyocr streamlit roboflow
   ```

2. **Get the dataset** — go to the **primary dataset** at
   `universe.roboflow.com/helmet-and-number-plate-detection-project/helmet-and-number-plate-detection-for-motorbike-safety-iityz`,
   select **YOLOv8** format, click "show download code", and copy the snippet (gives you an API key + download code). This single set gives you Bike / Helmet / No Helmet / Number Plate. Grab the **TVD** set only when you add triple riding as a model.

3. **Prove detection works** — run a pretrained model on any traffic image first:
   ```python
   from ultralytics import YOLO
   model = YOLO("yolov8n.pt")
   results = model("test_traffic.jpg")
   results[0].show()   # boxes should appear
   ```
   Once you see boxes, you know the pipeline is alive. Then swap in the helmet/triple-riding dataset and fine-tune.

4. **Lock scope today**: helmet + triple riding + plate OCR + challan agent. Resist adding more violations until the core loop demos end-to-end.

**Golden rule for the 5 days:** get a *thin end-to-end slice working first* (image in → annotated image + challan out, even if rough), THEN improve each stage. A complete rough pipeline beats a perfect detector with nothing attached to it.
