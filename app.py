"""Patra — Crop Disease Detection System (Flask web app)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, abort, g, jsonify, redirect, render_template, request, url_for

from analyzer import AnalysisError, analyze
from data import (
    DISEASE_BY_SLUG,
    DISEASES,
    FUTURE_SCOPE,
    HARDWARE,
    METHODOLOGY,
    PIPELINE,
    PROJECT,
    SOFTWARE,
    TEST_CASES,
)

BASE_DIR = Path(__file__).resolve().parent
FRAMES_DIR = BASE_DIR / "static" / "frames"
SAMPLES_DIR = BASE_DIR / "static" / "samples"
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
app.config["DATABASE"] = BASE_DIR / "instance" / "scans.db"

FRAME_COUNT = len(list(FRAMES_DIR.glob("*.webp"))) if FRAMES_DIR.exists() else 0
SAMPLES = [
    {"file": "sample-leaf-spot.jpg", "label": "Spotted soybean leaf"},
    {"file": "sample-blight.jpg", "label": "Leaf with necrotic lesions"},
    {"file": "sample-healthy.jpg", "label": "Healthy field leaf"},
]


# ---------------------------------------------------------------- database
def get_db() -> sqlite3.Connection:
    if "db" not in g:
        path: Path = app.config["DATABASE"]
        path.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(path)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc: BaseException | None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    with app.app_context():
        get_db().execute(
            """CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                filename TEXT,
                status TEXT NOT NULL,
                label TEXT NOT NULL,
                slug TEXT,
                confidence REAL,
                severity REAL,
                severity_band TEXT,
                features TEXT,
                thumbnail TEXT
            )"""
        )
        get_db().commit()


def save_scan(filename: str, result: dict) -> int:
    db = get_db()
    cur = db.execute(
        """INSERT INTO scans (created_at, filename, status, label, slug, confidence,
           severity, severity_band, features, thumbnail) VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
            filename[:120],
            result["status"],
            result["label"],
            result["slug"],
            result["confidence"],
            result["severity"],
            result["severity_band"],
            json.dumps(result["features"]),
            result["thumbnail"],
        ),
    )
    db.commit()
    return int(cur.lastrowid)


def scan_stats() -> dict:
    db = get_db()
    row = db.execute(
        """SELECT COUNT(*) AS total,
                  SUM(CASE WHEN slug = 'healthy' THEN 1 ELSE 0 END) AS healthy,
                  SUM(CASE WHEN status = 'ok' AND slug != 'healthy' THEN 1 ELSE 0 END) AS diseased,
                  AVG(CASE WHEN status = 'ok' THEN confidence END) AS avg_conf
           FROM scans"""
    ).fetchone()
    return {
        "total": row["total"] or 0,
        "healthy": row["healthy"] or 0,
        "diseased": row["diseased"] or 0,
        "avg_conf": round(row["avg_conf"], 1) if row["avg_conf"] is not None else None,
    }


# ---------------------------------------------------------------- template globals
@app.context_processor
def inject_globals() -> dict:
    return {"project": PROJECT, "nav_path": request.path, "year": datetime.now().year}


@app.template_filter("when")
def when_filter(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso).astimezone()
    except ValueError:
        return iso
    return dt.strftime("%d %b %Y · %H:%M")


# ---------------------------------------------------------------- pages
@app.get("/")
def home():
    return render_template(
        "index.html",
        frame_count=FRAME_COUNT,
        pipeline=PIPELINE,
        diseases=[d for d in DISEASES if d["slug"] != "healthy"][:5],
        page="home",
    )


@app.get("/detect")
def detect():
    return render_template("detect.html", samples=SAMPLES, page="detect")


@app.get("/diseases")
def diseases():
    types = sorted({d["type"] for d in DISEASES})
    return render_template("diseases.html", diseases=DISEASES, types=types, page="diseases")


@app.get("/diseases/<slug>")
def disease_detail(slug: str):
    disease = DISEASE_BY_SLUG.get(slug)
    if disease is None:
        abort(404)
    idx = DISEASES.index(disease)
    nxt = DISEASES[(idx + 1) % len(DISEASES)]
    return render_template("disease.html", d=disease, nxt=nxt, page="diseases")


@app.get("/how-it-works")
def how_it_works():
    return render_template(
        "how.html",
        pipeline=PIPELINE,
        methodology=METHODOLOGY,
        hardware=HARDWARE,
        software=SOFTWARE,
        test_cases=TEST_CASES,
        page="how",
    )


@app.get("/project")
def project():
    return render_template("project.html", future=FUTURE_SCOPE, page="project")


@app.get("/history")
def history():
    rows = get_db().execute("SELECT * FROM scans ORDER BY id DESC LIMIT 100").fetchall()
    scans = [dict(r) | {"features": json.loads(r["features"] or "{}")} for r in rows]
    return render_template("history.html", scans=scans, stats=scan_stats(), page="history")


@app.post("/history/clear")
def clear_history():
    db = get_db()
    db.execute("DELETE FROM scans")
    db.commit()
    return redirect(url_for("history"))


# ---------------------------------------------------------------- api
@app.post("/api/analyze")
def api_analyze():
    upload = request.files.get("image")
    if upload is None or upload.filename == "":
        return jsonify(error="Attach a leaf photo in the 'image' field."), 400
    if Path(upload.filename).suffix.lower() not in ALLOWED_EXT:
        return jsonify(error="Unsupported file type. Use JPG, PNG or WebP."), 415
    try:
        result = analyze(upload.read()).to_dict()
    except AnalysisError as exc:
        return jsonify(error=str(exc)), 422
    result["scan_id"] = save_scan(upload.filename, result)
    disease = DISEASE_BY_SLUG.get(result["slug"])
    result["advice"] = (
        {
            "summary": disease["summary"],
            "type": disease["type"],
            "pathogen": disease["pathogen"],
            "steps": next(iter(disease["management"].values()))[:3],
            "url": url_for("disease_detail", slug=disease["slug"]),
        }
        if disease
        else None
    )
    result.pop("thumbnail", None)
    return jsonify(result)


@app.get("/api/scans")
def api_scans():
    rows = get_db().execute(
        "SELECT id, created_at, filename, status, label, slug, confidence, severity, severity_band "
        "FROM scans ORDER BY id DESC LIMIT 50"
    ).fetchall()
    return jsonify(scans=[dict(r) for r in rows], stats=scan_stats())


@app.get("/api/health")
def api_health():
    return jsonify(status="ok", frames=FRAME_COUNT, classes=7)


# ---------------------------------------------------------------- errors
@app.errorhandler(404)
def not_found(_e):
    return render_template("404.html", page="404"), 404


@app.errorhandler(413)
def too_large(_e):
    return jsonify(error="Image is larger than 10 MB. Resize it and try again."), 413


init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
