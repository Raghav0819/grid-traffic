"""
Streamlit demo for the GRiD Traffic Violation system.

Run:
  streamlit run app.py

Flow: upload image -> detect violations -> annotated evidence -> read plate ->
generate bilingual e-challan -> log to session analytics.
"""
import os
from datetime import datetime

import cv2
import numpy as np
import streamlit as st
from PIL import Image

import config
from detector import ViolationDetector
from ocr import read_plate
from challan_agent import generate_challan

st.set_page_config(page_title="Bangalore Traffic Violation AI", layout="wide")


# ── model loader (cached across reruns) ───────────────────────────────────
@st.cache_resource
def load_detector():
    return ViolationDetector()


# ── session analytics store ────────────────────────────────────────────────
if "log" not in st.session_state:
    st.session_state.log = []

st.title("🚦 Agentic Traffic Violation Detection & E-Challan")
st.caption("Flipkart GRiD — Theme 3 | YOLO + OCR + RAG E-Challan | Bangalore Traffic AI")

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    conf_slider = st.slider(
        "Detection confidence threshold", 0.05, 0.80,
        float(config.CONF_THRESHOLD), 0.05,
        help="Lower = more detections (more false positives). "
             "Higher = fewer but more confident detections.",
    )
    show_raw = st.checkbox(
        "Show raw YOLO detections (debug)",
        help="Displays ALL model detections before violation logic is applied.",
    )

    st.divider()
    st.header("🤖 Models")
    st.markdown(f"**Primary:** `{config.MODEL_PATH}`")
    tvd_path = getattr(config, "TVD_MODEL_PATH", "best_tvd.pt")
    if os.path.exists(tvd_path):
        st.markdown(f"**TVD:** `{tvd_path}` ✅")
    else:
        st.markdown(f"**TVD:** `{tvd_path}` ❌ *(not trained yet)*")
        st.caption("Triple riding uses logic-based head-count fallback.")

    st.divider()
    st.header("📊 Session")
    st.metric("Images processed", len({e["time"] for e in st.session_state.log}))
    st.metric("Violations logged", len(st.session_state.log))
    if st.button("🗑️ Clear session log"):
        st.session_state.log = []
        st.rerun()

# ── Tabs ───────────────────────────────────────────────────────────────────
tab_detect, tab_analytics = st.tabs(["🔍 Detect", "📈 Analytics"])

# ═══════════════════════════ DETECT TAB ═══════════════════════════════════
with tab_detect:
    detector = load_detector()
    detector.conf = conf_slider

    uploaded = st.file_uploader(
        "Upload a traffic image", type=["jpg", "jpeg", "png"],
        help="Best results with clear daylight images showing two-wheelers.",
    )

    if uploaded:
        pil = Image.open(uploaded).convert("RGB")
        img_bgr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

        # ── run detection ─────────────────────────────────────────────────
        with st.spinner("Running violation detection..."):
            annotated, records = detector.detect(img_bgr)

        # ── debug: raw YOLO boxes ─────────────────────────────────────────
        if show_raw:
            with st.spinner("Generating raw detection overlay..."):
                raw_results = detector.model(img_bgr, conf=conf_slider, verbose=False)[0]
                raw_img = raw_results.plot()

            st.subheader("🔍 Raw YOLO detections (all classes, before violation logic)")

            tvd_model = getattr(detector, "tvd_model", None)
            if tvd_model:
                dcol1, dcol2 = st.columns(2)
                with dcol1:
                    st.caption(f"**Primary model** — {len(raw_results.boxes)} boxes")
                    st.image(cv2.cvtColor(raw_img, cv2.COLOR_BGR2RGB),
                             use_container_width=True)
                with dcol2:
                    tvd_conf = getattr(detector, "tvd_conf", 0.35)
                    tvd_results = tvd_model(img_bgr, conf=tvd_conf, verbose=False)[0]
                    tvd_img = tvd_results.plot()
                    st.caption(f"**TVD model** — {len(tvd_results.boxes)} boxes")
                    st.image(cv2.cvtColor(tvd_img, cv2.COLOR_BGR2RGB),
                             use_container_width=True)
            else:
                st.image(cv2.cvtColor(raw_img, cv2.COLOR_BGR2RGB),
                         use_container_width=True)
                st.caption(f"{len(raw_results.boxes)} raw boxes at conf ≥ {conf_slider:.2f}")
            st.divider()

        # ── main output columns ───────────────────────────────────────────
        col1, col2 = st.columns([3, 2])

        with col1:
            st.subheader("📸 Annotated Evidence")
            st.image(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB),
                     use_container_width=True)

        with col2:
            violation_count = len(records)
            if violation_count == 0:
                st.success("✅ No violations detected in this image.")
            else:
                st.error(f"🚨 {violation_count} violation(s) detected")

            for i, r in enumerate(records, 1):
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # ── OCR ───────────────────────────────────────────────────
                with st.spinner(f"Reading plate for vehicle {i}..."):
                    plate_result = read_plate(img_bgr, r["plate_box"])

                plate    = plate_result["plate"]
                pdisplay = plate_result["display"]
                pfmt     = plate_result["format"]
                pengine  = plate_result["engine"]
                pconf    = plate_result["conf"]

                # ── challan ───────────────────────────────────────────────
                with st.spinner("Generating e-challan..."):
                    challan = generate_challan(plate, r["violations"], ts)

                viol_label = ", ".join(
                    v.replace("_", " ").title() for v in r["violations"]
                )

                with st.expander(f"Vehicle {i} — {viol_label}", expanded=True):

                    # plate info row
                    pcol1, pcol2 = st.columns([2, 1])
                    with pcol1:
                        st.markdown(f"**🔢 Plate:** `{pdisplay}`")
                        st.caption(f"Format: {pfmt} · Engine: {pengine} · Conf: {pconf:.2f}")
                    with pcol2:
                        st.metric("Riders", r["rider_count"])

                    st.markdown(f"**💰 Total Fine:** ₹ {challan['total_fine']}")
                    st.divider()

                    # challan tabs
                    ctab_en, ctab_hi = st.tabs(["English Challan", "हिंदी चालान"])
                    with ctab_en:
                        st.text_area("", challan["english"],
                                     height=180, key=f"en_{i}",
                                     label_visibility="collapsed")
                    with ctab_hi:
                        if challan.get("hindi"):
                            st.text_area("", challan["hindi"],
                                         height=180, key=f"hi_{i}",
                                         label_visibility="collapsed")
                        else:
                            st.info("Hindi challan unavailable (set GEMINI_API_KEY to enable).")

                # ── log to analytics ──────────────────────────────────────
                st.session_state.log.append({
                    "time":       ts,
                    "plate":      pdisplay,
                    "format":     pfmt,
                    "violations": r["violations"],
                    "riders":     r["rider_count"],
                    "fine":       challan["total_fine"],
                })

# ═══════════════════════════ ANALYTICS TAB ════════════════════════════════
with tab_analytics:
    st.subheader("📈 Session Analytics")
    log = st.session_state.log

    if not log:
        st.info("No violations logged yet — process some images in the Detect tab.")
    else:
        total_fine = sum(e["fine"] for e in log)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total violations",  len(log))
        c2.metric("Unique vehicles",   len({e["plate"] for e in log}))
        c3.metric("Total fines (₹)",   f"₹{total_fine:,}")
        c4.metric("Avg fine / vehicle",
                  f"₹{total_fine // max(len({e['plate'] for e in log}), 1):,}")

        st.divider()

        # violation-type breakdown
        st.markdown("#### Violation breakdown")
        counts: dict[str, int] = {}
        for e in log:
            for v in e["violations"]:
                label = v.replace("_", " ").title()
                counts[label] = counts.get(label, 0) + 1
        st.bar_chart(counts)

        # plate format breakdown
        st.markdown("#### Plate format distribution")
        fmt_counts: dict[str, int] = {}
        for e in log:
            fmt = e.get("format", "unknown")
            fmt_counts[fmt] = fmt_counts.get(fmt, 0) + 1
        st.bar_chart(fmt_counts)

        st.divider()

        # searchable records table
        st.markdown("#### Searchable records")
        q = st.text_input("🔍 Search by plate number")
        rows = [e for e in log if q.upper() in e["plate"].upper()] if q else log
        st.dataframe(
            [
                {
                    "Time":       e["time"],
                    "Plate":      e["plate"],
                    "Format":     e.get("format", ""),
                    "Violations": ", ".join(e["violations"]),
                    "Riders":     e.get("riders", "-"),
                    "Fine (₹)":   e["fine"],
                }
                for e in rows
            ],
            use_container_width=True,
        )