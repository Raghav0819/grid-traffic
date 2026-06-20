"use client";

import { useState, useEffect, useCallback } from "react";
import { getHistory } from "@/lib/api";

interface ViolationRecord {
  id: number;
  timestamp: string;
  plate: string;
  display: string;
  plate_fmt: string;
  violations: string[];
  riders: number;
  fine: number;
  engine: string;
  conf: number;
  image_hash: string;
}

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function HistoryPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ViolationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [imageModal, setImageModal] = useState<string | null>(null);

  const fetchHistory = useCallback(async (q: string = "") => {
    setLoading(true);
    setError(null);
    try {
      const data = await getHistory(q);
      setResults(data.results || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load history");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchHistory(query);
  };

  return (
    <div className="page-container">
      <div className="page-header animate-in">
        <h1><span className="gradient-text">Vehicle History</span></h1>
        <p>Search past violations by license plate number.</p>
      </div>

      {/* Search bar */}
      <form onSubmit={handleSearch} className="animate-in animate-in-delay-1" style={{ display: "flex", gap: 12, marginBottom: 32 }}>
        <input
          className="input"
          placeholder="Search by plate number (e.g., KA 01 AB 1234)..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{ flex: 1 }}
        />
        <button type="submit" className="btn btn-primary">🔍 Search</button>
        {query && (
          <button type="button" className="btn btn-ghost" onClick={() => { setQuery(""); fetchHistory(); }}>
            Clear
          </button>
        )}
      </form>

      {/* Error */}
      {error && (
        <div className="glass-strong animate-in" style={{ padding: 20, textAlign: "center" }}>
          <span style={{ color: "var(--color-danger)" }}>⚠️ {error}</span>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div style={{ textAlign: "center", padding: 40 }}>
          <div className="spinner" style={{ margin: "0 auto 12px" }} />
          <div className="loading-text">Loading records...</div>
        </div>
      )}

      {/* Results table */}
      {!loading && !error && (
        <div className="glass-strong animate-in animate-in-delay-2" style={{ overflow: "hidden" }}>
          <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--glass-border)" }}>
            <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
              {results.length} record{results.length !== 1 ? "s" : ""} found
              {query && ` for "${query}"`}
            </span>
          </div>

          {results.length === 0 ? (
            <div style={{ padding: 40, textAlign: "center" }}>
              <div style={{ fontSize: "2.5rem", marginBottom: 12 }}>🔍</div>
              <p style={{ color: "var(--text-muted)" }}>
                {query ? `No violations found for "${query}".` : "No violations recorded yet. Process some images first."}
              </p>
            </div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Plate</th>
                    <th>Format</th>
                    <th>Violations</th>
                    <th>Riders</th>
                    <th>Fine (₹)</th>
                    <th>Engine</th>
                    <th>Conf</th>
                    <th>Image</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r) => (
                    <tr key={r.id}>
                      <td className="mono" style={{ fontSize: "0.8rem" }}>{r.timestamp}</td>
                      <td>
                        <span className="mono" style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                          {r.display || r.plate || "—"}
                        </span>
                      </td>
                      <td>
                        <span className="badge badge-info">{r.plate_fmt}</span>
                      </td>
                      <td>
                        <div className="flex gap-8" style={{ flexWrap: "wrap" }}>
                          {r.violations.map((v) => (
                            <span key={v} className="badge badge-danger">
                              {v.replace(/_/g, " ")}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td style={{ textAlign: "center" }}>{r.riders}</td>
                      <td style={{ fontWeight: 700, color: "var(--color-danger)" }}>₹{r.fine}</td>
                      <td><span className="badge badge-info">{r.engine || "—"}</span></td>
                      <td>{(r.conf * 100).toFixed(0)}%</td>
                      <td>
                        {r.image_hash && (
                          <button
                            className="btn btn-ghost btn-sm"
                            onClick={() => setImageModal(r.image_hash)}
                          >
                            📷 View
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Image Modal */}
      {imageModal && (
        <div className="modal-overlay" onClick={() => setImageModal(null)}>
          <div className="modal glass-strong" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 900 }}>
            <div className="modal-header">
              <h3>📸 Violation Evidence</h3>
              <button className="modal-close" onClick={() => setImageModal(null)}>✕</button>
            </div>
            <div style={{ textAlign: "center" }}>
              <img
                src={`${API}/api/image/${imageModal}`}
                alt="Violation evidence"
                style={{ maxWidth: "100%", maxHeight: "70vh", borderRadius: "var(--radius-md)" }}
              />
            </div>
            <div className="flex gap-12" style={{ marginTop: 20, justifyContent: "flex-end" }}>
              <button className="btn btn-ghost" onClick={() => setImageModal(null)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
