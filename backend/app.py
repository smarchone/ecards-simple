from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# Simple Flask API to store e-card drafts (including template URI) on the backend.
# Storage: local JSON file backend/data/drafts.json
# Endpoints:
#   GET  /api/health
#   POST /api/drafts             - create or update a draft (if id provided)
#   GET  /api/drafts/<draft_id>    - fetch a draft by id
#
# Draft schema (JSON):
# {
#   "id": "draft_123" | "d_<uuid>",  # optional on create, required on update
#   "title": "My e-card",
#   "updatedAt": 1725360000000,          # epoch millis (server can set if omitted)
#   "template": "assets/template1.png",  # template URI/path
#   "canvasSize": { "w": 900, "h": 600 },
#   "data": {}                           # fabric.js JSON payload
# }

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_FILE = DATA_DIR / "drafts.json"

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Serve frontend (index.html) and assets from project root so UI and API share the same origin/port
ROOT_DIR = (Path(__file__).resolve().parents[1])

@app.get("/")
def serve_index():
    return send_from_directory(ROOT_DIR, "index.html")

@app.get("/assets/<path:filename>")
def serve_assets(filename: str):
    return send_from_directory(ROOT_DIR / "assets", filename)


def _now_ms() -> int:
    return int(datetime.now(tz=timezone.utc).timestamp() * 1000)


def load_db() -> Dict[str, Any]:
    if not DB_FILE.exists():
        return {"drafts": {}}
    try:
        with DB_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Corrupt file fallback
        return {"drafts": {}}


def save_db(db: Dict[str, Any]) -> None:
    tmp = DB_FILE.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    tmp.replace(DB_FILE)


@app.get("/api/health")
def health():
    return jsonify({"ok": True})


@app.post("/api/drafts")
def create_or_update_draft():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid JSON"}), 400

    draft_id: Optional[str] = payload.get("id") or None
    if not draft_id:
        draft_id = f"d_{uuid4().hex}"

    # Normalize and validate minimal fields
    title = payload.get("title") or "Untitled ecard"
    updated_at = payload.get("updatedAt")
    if not isinstance(updated_at, int):
        updated_at = _now_ms()

    template = payload.get("template")  # can be None
    canvas_size = payload.get("canvasSize") or {}
    if not isinstance(canvas_size, dict):
        canvas_size = {}
    data = payload.get("data") or {}

    # Persist
    db = load_db()
    db.setdefault("drafts", {})
    db["drafts"][draft_id] = {
        "id": draft_id,
        "title": title,
        "updatedAt": updated_at,
        "template": template,
        "canvasSize": {
            "w": int(canvas_size.get("w") or 900),
            "h": int(canvas_size.get("h") or 600),
        },
        "data": data,
    }
    save_db(db)

    return jsonify({"id": draft_id})


@app.get("/api/drafts/<draft_id>")
def get_draft(draft_id: str):
    db = load_db()
    draft = db.get("drafts", {}).get(draft_id)
    if not draft:
        return jsonify({"error": "Not found"}), 404
    return jsonify(draft)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))
    # 0.0.0.0 so it can be accessed from host if containerized later
    app.run(host="0.0.0.0", port=port, debug=True)