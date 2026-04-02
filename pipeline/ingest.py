"""
Ingest stage: reads source JSON files and returns raw data with source metadata.

Each source record carries: path, filename, source_type, source_hash, ingested_at, data.
The source_hash covers the full file content so downstream stages can detect changes.
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone


# Maps known filenames to semantic source types consumed by later stages.
SOURCES = {
    "base_coren.json": "knowledge_base",
    "programação ia.json": "ia_config",
}


def load_source(path: Path) -> dict:
    """Load a single JSON file and attach ingest metadata."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    raw_bytes = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return {
        "path": str(path),
        "filename": path.name,
        "source_type": SOURCES.get(path.name, "unknown"),
        "source_hash": hashlib.sha256(raw_bytes).hexdigest(),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }


def ingest_all(root: Path) -> list:
    """Ingest all known sources found under *root*."""
    results = []
    for filename in SOURCES:
        path = root / filename
        if path.exists():
            results.append(load_source(path))
    return results
