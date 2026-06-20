"use client";

import { useState, useRef, useCallback } from "react";
import { detect, downloadPdf } from "@/lib/api";

/* ── Types ─────────────────────────────────────────────────────────────── */
interface PlateInfo {
  text: string;
  display: string;
  format: string;
  engine: string;
  conf: number;
}
interface ChallanInfo {
  english: string;
  hindi: string;
  total_fine: number;
}
interface ViolationResult {
  vehicle_id: number;
  plate: PlateInfo;
  violations: string[];
  rider_count: number;
  challan: ChallanInfo;
  facts: Record<string, Record<string, unknown> | null>;
}
interface DetectResponse {
  annotated_image: string;
  original_image: string;
  violation_count: number;
  timestamp: string;
  results: ViolationResult[];
}

/* ── Page Component ────────────────────────────────────────────────────── */
export default function DetectPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<DetectResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [challanModal, setChallanModal] = useState<ViolationResult | null>(null);
  const [challanTab, setChallanTab] = useState<"en" | "hi">("en");
  const [zoom, setZoom] = useState(1);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((f: File) => {
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setData(null);
    setError(null);
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const f = e.dataTransfer.files[0];
      if (f && f.type.startsWith("image/")) handleFile(f);
    },
    [handleFile]
  );

  const runDetection = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const result = await detect(file);
      setData(result);
      setZoom(1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Detection failed");
    } finally {
      setLoading(false);
    }
  };

  const handlePdfDownload = async (r: ViolationResult, ts: string) => {
    try {
      const blob = await downloadPdf({
        plate: r.plate.display,
        violations: r.violations,
        total_fine: r.challan.total_fine,
        timestamp: ts,
        riders: r.rider_count,
        facts: r.facts as Record<string, unknown>,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `challan_${r.plate.display.replace(/\s/g, "_") || "unknown"}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert("PDF generation failed. Is the backend running?");
    }
  };

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header animate-in">
        <h1>
          <span className="gradient-text">Violation Detection</span>
        </h1>
        <p>Upload a traffic image to detect helmet violations, triple riding, and more.</p>
      </div>

      {/* Drop Zone */}
      {!data && (
        <div
          className={`dropzone glass animate-in animate-in-delay-1 ${dragOver ? "drag-over" : ""}`}
          onClick={() => fileRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          style={{ position: "relative" }}
        >
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            style={{ display: "none" }}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
            }}
          />
          {preview ? (
            <div style={{ position: "relative", zIndex: 1 }}>
              <img src={preview} alt="Preview" className="dz-preview" />
              <p className="dz-subtitle" style={{ marginTop: 12 }}>
                {file?.name} — Click &ldquo;Detect Violations&rdquo; to analyze
              </p>
            </div>
          ) : (
            <div style={{ position: "relative", zIndex: 1 }}>
              <div className="dz-icon">📸</div>
              <div className="dz-title">Drop an image here or click to browse</div>
              <div className="dz-subtitle">Supports JPG, JPEG, PNG — best with daylight two-wheeler photos</div>
            </div>
          )}
        </div>
      )}

      {/* Detect Button */}
      {file && !data && (
        <div className="animate-in animate-in-delay-2" style={{ textAlign: "center", marginTop: 24 }}>
          <button className="btn btn-primary btn-lg" onClick={runDetection} disabled={loading}>
            {loading ? (
              <>
                <span className="spinner" /> Analyzing...
              </>
            ) : (
              "🔍 Detect Violations"
            )}
          </button>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="glass-strong animate-in" style={{ padding: 20, marginTop: 24, textAlign: "center" }}>
          <span style={{ color: "var(--color-danger)" }}>⚠️ {error}</span>
          <p style={{ color: "var(--text-muted)", marginTop: 8, fontSize: "0.85rem" }}>
            Make sure the backend is running: <code className="mono">uvicorn server:app --port 8000</code>
          </p>
        </div>
      )}

      {/* Loading overlay */}
      {loading && (
        <div className="glass-strong animate-in" style={{ padding: 60, marginTop: 24, textAlign: "center" }}>
          <div className="spinner spinner-lg" style={{ margin: "0 auto 16px" }} />
          <div className="loading-text">Running YOLO detection + OCR + RAG challan...</div>
        </div>
      )}

      {/* Results */}
      {data && (
        <div className="animate-in" style={{ marginTop: 24 }}>
          {/* Stats row */}
          <div className="grid-3" style={{ marginBottom: 24 }}>
            <div className="stat-card glass animate-in animate-in-delay-1">
              <div className="stat-icon" style={{ background: "rgba(239,68,68,0.15)" }}>🚨</div>
              <div className="stat-label">Violations</div>
              <div className="stat-value" style={{ color: data.violation_count > 0 ? "var(--color-danger)" : "var(--color-success)" }}>
                {data.violation_count}
              </div>
            </div>
            <div className="stat-card glass animate-in animate-in-delay-2">
              <div className="stat-icon" style={{ background: "rgba(59,130,246,0.15)" }}>🕐</div>
              <div className="stat-label">Timestamp</div>
              <div className="stat-value" style={{ fontSize: "1rem" }}>{data.timestamp}</div>
            </div>
            <div className="stat-card glass animate-in animate-in-delay-3">
              <div className="stat-icon" style={{ background: "rgba(16,185,129,0.15)" }}>💰</div>
              <div className="stat-label">Total Fines</div>
              <div className="stat-value gradient-text">
                ₹{data.results.reduce((s, r) => s + r.challan.total_fine, 0).toLocaleString()}
              </div>
            </div>
          </div>

          {/* Image + Violations */}
          <div style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr", gap: 24 }}>
            {/* Annotated image */}
            <div className="glass-strong animate-in animate-in-delay-1" style={{ padding: 16 }}>
              <div className="flex items-center justify-between mb-16">
                <h3>📸 Annotated Evidence</h3>
                <div className="flex gap-8">
                  <button className="btn btn-ghost btn-sm" onClick={() => setZoom((z) => Math.max(0.5, z - 0.25))}>−</button>
                  <span className="mono" style={{ fontSize: "0.8rem", color: "var(--text-muted)", minWidth: 40, textAlign: "center" }}>
                    {Math.round(zoom * 100)}%
                  </span>
                  <button className="btn btn-ghost btn-sm" onClick={() => setZoom((z) => Math.min(3, z + 0.25))}>+</button>
                  <button className="btn btn-ghost btn-sm" onClick={() => setZoom(1)}>Reset</button>
                </div>
              </div>
              <div className="image-viewer" style={{ overflow: "auto", maxHeight: 600 }}>
                <img
                  src={`data:image/jpeg;base64,${data.annotated_image}`}
                  alt="Annotated evidence"
                  style={{ transform: `scale(${zoom})`, transformOrigin: "top left" }}
                  draggable={false}
                />
              </div>
            </div>

            {/* Violation cards */}
            <div className="flex flex-col gap-16">
              {data.violation_count === 0 ? (
                <div className="glass-strong animate-in" style={{ padding: 40, textAlign: "center" }}>
                  <div style={{ fontSize: "3rem", marginBottom: 12 }}>✅</div>
                  <h3>No Violations Detected</h3>
                  <p style={{ color: "var(--text-muted)", marginTop: 8 }}>
                    All riders appear to be following traffic rules.
                  </p>
                </div>
              ) : (
                data.results.map((r, idx) => (
                  <div key={idx} className={`violation-card glass-strong animate-in animate-in-delay-${idx + 1}`}>
                    <div className="vc-header">
                      <span className="vc-vehicle-id">Vehicle {r.vehicle_id}</span>
                      <div className="flex gap-8">
                        {r.violations.map((v) => (
                          <span key={v} className="badge badge-danger">
                            {v.replace(/_/g, " ")}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="vc-plate">{r.plate.display || "NOT READABLE"}</div>

                    <div className="vc-detail-row">
                      <span className="vc-detail-label">OCR Engine</span>
                      <span className="vc-detail-value badge badge-info">{r.plate.engine}</span>
                    </div>
                    <div className="vc-detail-row">
                      <span className="vc-detail-label">Confidence</span>
                      <span className="vc-detail-value">{(r.plate.conf * 100).toFixed(1)}%</span>
                    </div>
                    <div className="vc-detail-row">
                      <span className="vc-detail-label">Plate Format</span>
                      <span className="vc-detail-value">{r.plate.format}</span>
                    </div>
                    <div className="vc-detail-row">
                      <span className="vc-detail-label">Riders</span>
                      <span className="vc-detail-value">{r.rider_count}</span>
                    </div>

                    <div className="vc-fine">₹{r.challan.total_fine.toLocaleString()}</div>

                    <div className="vc-actions">
                      <button className="btn btn-primary btn-sm" onClick={() => { setChallanModal(r); setChallanTab("en"); }}>
                        📄 View Challan
                      </button>
                      <button className="btn btn-success btn-sm" onClick={() => handlePdfDownload(r, data.timestamp)}>
                        ⬇ Download PDF
                      </button>
                    </div>
                  </div>
                ))
              )}

              {/* New image button */}
              <button
                className="btn btn-ghost w-full"
                onClick={() => { setData(null); setFile(null); setPreview(null); }}
              >
                📷 Analyze Another Image
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Challan Modal */}
      {challanModal && (
        <div className="modal-overlay" onClick={() => setChallanModal(null)}>
          <div className="modal glass-strong" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>E-Challan — Vehicle {challanModal.vehicle_id}</h3>
              <button className="modal-close" onClick={() => setChallanModal(null)}>✕</button>
            </div>

            <div className="tabs">
              <button className={`tab ${challanTab === "en" ? "active" : ""}`} onClick={() => setChallanTab("en")}>
                English
              </button>
              <button className={`tab ${challanTab === "hi" ? "active" : ""}`} onClick={() => setChallanTab("hi")}>
                हिंदी
              </button>
            </div>

            <div className="challan-text">
              {challanTab === "en"
                ? challanModal.challan.english
                : challanModal.challan.hindi || "Hindi challan not available."}
            </div>

            <div className="flex gap-12" style={{ marginTop: 20, justifyContent: "flex-end" }}>
              <button
                className="btn btn-success"
                onClick={() => data && handlePdfDownload(challanModal, data.timestamp)}
              >
                ⬇ Download PDF
              </button>
              <button className="btn btn-ghost" onClick={() => setChallanModal(null)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
