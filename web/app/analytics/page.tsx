"use client";

import { useState, useEffect } from "react";
import { getAnalytics } from "@/lib/api";

interface Stats {
  total_violations: number;
  unique_vehicles: number;
  total_fines: number;
  avg_fine: number;
  violation_types: Record<string, number>;
  engine_breakdown: Record<string, number>;
  format_breakdown: Record<string, number>;
}

function BarChart({ data, color }: { data: Record<string, number>; color?: string }) {
  const max = Math.max(...Object.values(data), 1);
  return (
    <div className="bar-chart">
      {Object.entries(data).map(([label, value]) => (
        <div className="bar-row" key={label}>
          <span className="bar-label">{label}</span>
          <div className="bar-track">
            <div
              className="bar-fill"
              style={{
                width: `${(value / max) * 100}%`,
                background: color || "var(--gradient-primary)",
              }}
            >
              {value}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function AnalyticsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAnalytics()
      .then(setStats)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="page-container" style={{ textAlign: "center", paddingTop: 100 }}>
        <div className="spinner spinner-lg" style={{ margin: "0 auto 16px" }} />
        <div className="loading-text">Loading analytics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="glass-strong" style={{ padding: 40, marginTop: 60, textAlign: "center" }}>
          <p style={{ color: "var(--color-danger)" }}>⚠️ {error}</p>
          <p style={{ color: "var(--text-muted)", marginTop: 8, fontSize: "0.85rem" }}>
            Make sure the backend is running: <code className="mono">uvicorn server:app --port 8000</code>
          </p>
        </div>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="page-container">
      <div className="page-header animate-in">
        <h1><span className="gradient-text">Analytics Dashboard</span></h1>
        <p>Real-time violation statistics from processed images.</p>
      </div>

      {/* Stat Cards */}
      <div className="grid-4" style={{ marginBottom: 32 }}>
        <div className="stat-card glass animate-in animate-in-delay-1">
          <div className="stat-icon" style={{ background: "rgba(239,68,68,0.15)" }}>🚨</div>
          <div className="stat-label">Total Violations</div>
          <div className="stat-value" style={{ color: "var(--color-danger)" }}>{stats.total_violations}</div>
        </div>
        <div className="stat-card glass animate-in animate-in-delay-2">
          <div className="stat-icon" style={{ background: "rgba(59,130,246,0.15)" }}>🏍️</div>
          <div className="stat-label">Unique Vehicles</div>
          <div className="stat-value">{stats.unique_vehicles}</div>
        </div>
        <div className="stat-card glass animate-in animate-in-delay-3">
          <div className="stat-icon" style={{ background: "rgba(16,185,129,0.15)" }}>💰</div>
          <div className="stat-label">Total Fines</div>
          <div className="stat-value gradient-text">₹{stats.total_fines.toLocaleString()}</div>
        </div>
        <div className="stat-card glass animate-in animate-in-delay-4">
          <div className="stat-icon" style={{ background: "rgba(245,158,11,0.15)" }}>📊</div>
          <div className="stat-label">Avg Fine / Vehicle</div>
          <div className="stat-value">₹{stats.avg_fine.toLocaleString()}</div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid-2" style={{ marginBottom: 32 }}>
        <div className="glass-strong p-24 animate-in animate-in-delay-2">
          <h3 className="mb-16">Violation Type Breakdown</h3>
          {Object.keys(stats.violation_types).length > 0 ? (
            <BarChart data={stats.violation_types} />
          ) : (
            <p style={{ color: "var(--text-muted)" }}>No violations recorded yet.</p>
          )}
        </div>

        <div className="glass-strong p-24 animate-in animate-in-delay-3">
          <h3 className="mb-16">OCR Engine Usage</h3>
          {Object.keys(stats.engine_breakdown).length > 0 ? (
            <BarChart data={stats.engine_breakdown} color="var(--gradient-accent)" />
          ) : (
            <p style={{ color: "var(--text-muted)" }}>No data yet.</p>
          )}
        </div>
      </div>

      <div className="glass-strong p-24 animate-in animate-in-delay-4">
        <h3 className="mb-16">Plate Format Distribution</h3>
        {Object.keys(stats.format_breakdown).length > 0 ? (
          <BarChart data={stats.format_breakdown} color="var(--gradient-success)" />
        ) : (
          <p style={{ color: "var(--text-muted)" }}>No plate data yet.</p>
        )}
      </div>
    </div>
  );
}
