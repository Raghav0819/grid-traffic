"""
SQLite persistence for violation history.

Tables:
  violations — one row per vehicle violation record
"""
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "violations.db")

def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    """Create tables if they don't exist."""
    conn = _conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS violations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            plate       TEXT    NOT NULL DEFAULT '',
            display     TEXT    NOT NULL DEFAULT '',
            plate_fmt   TEXT    NOT NULL DEFAULT 'unknown',
            violations  TEXT    NOT NULL DEFAULT '[]',
            riders      INTEGER NOT NULL DEFAULT 1,
            fine        INTEGER NOT NULL DEFAULT 0,
            engine      TEXT    NOT NULL DEFAULT '',
            conf        REAL    NOT NULL DEFAULT 0.0,
            image_hash  TEXT    NOT NULL DEFAULT ''
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_plate ON violations(plate)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_ts ON violations(timestamp)
    """)
    conn.commit()
    conn.close()

def log_violation(
    plate: str,
    display: str,
    plate_fmt: str,
    violations: list[str],
    riders: int,
    fine: int,
    engine: str = "",
    conf: float = 0.0,
    image_hash: str = "",
    timestamp: str = None,
) -> int:
    """Insert a violation record. Returns the new row id."""
    ts = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = _conn()
    cur = conn.execute(
        """INSERT INTO violations
           (timestamp, plate, display, plate_fmt, violations, riders, fine, engine, conf, image_hash)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (ts, plate, display, plate_fmt, json.dumps(violations), riders, fine, engine, conf, image_hash),
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id

def search_by_plate(query: str, limit: int = 50) -> list[dict]:
    """Search violations by plate substring (case-insensitive)."""
    conn = _conn()
    rows = conn.execute(
        """SELECT * FROM violations
           WHERE plate LIKE ? OR display LIKE ?
           ORDER BY timestamp DESC LIMIT ?""",
        (f"%{query}%", f"%{query}%", limit),
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]

def get_all(limit: int = 200) -> list[dict]:
    """Return recent violations."""
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM violations ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]

def get_stats() -> dict:
    """Aggregate stats for the analytics dashboard."""
    conn = _conn()
    total = conn.execute("SELECT COUNT(*) FROM violations").fetchone()[0]
    unique_plates = conn.execute(
        "SELECT COUNT(DISTINCT plate) FROM violations WHERE plate != ''"
    ).fetchone()[0]
    total_fines = conn.execute(
        "SELECT COALESCE(SUM(fine), 0) FROM violations"
    ).fetchone()[0]

    # Violation type breakdown
    rows = conn.execute("SELECT violations FROM violations").fetchall()
    type_counts = {}
    for r in rows:
        for v in json.loads(r[0]):
            label = v.replace("_", " ").title()
            type_counts[label] = type_counts.get(label, 0) + 1

    # Engine breakdown
    engine_rows = conn.execute(
        "SELECT engine, COUNT(*) as cnt FROM violations GROUP BY engine"
    ).fetchall()
    engine_counts = {r[0] or "none": r[1] for r in engine_rows}

    # Format breakdown
    fmt_rows = conn.execute(
        "SELECT plate_fmt, COUNT(*) as cnt FROM violations GROUP BY plate_fmt"
    ).fetchall()
    fmt_counts = {r[0]: r[1] for r in fmt_rows}

    conn.close()
    return {
        "total_violations": total,
        "unique_vehicles": unique_plates,
        "total_fines": total_fines,
        "avg_fine": total_fines // max(unique_plates, 1),
        "violation_types": type_counts,
        "engine_breakdown": engine_counts,
        "format_breakdown": fmt_counts,
    }

def _row_to_dict(row) -> dict:
    d = dict(row)
    d["violations"] = json.loads(d["violations"])
    return d

# Auto-init on import
init_db()
