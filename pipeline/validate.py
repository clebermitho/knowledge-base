"""
Validate stage: structural quality checks on generated artifacts.

These checks run after publish and act as the pipeline's acceptance gate.
They verify minimum metadata presence, chunk integrity, and manifest
completeness.  A validation failure exits the pipeline with a non-zero code
so CI catches regressions immediately.
"""
import json
from pathlib import Path


DIST_DIR = Path("dist")

REQUIRED_CHUNK_FIELDS = {"id", "source", "category", "text", "response", "hash", "version"}
REQUIRED_META_FIELDS = {"version", "generated_at", "total_chunks", "sources", "pipeline_hash"}
REQUIRED_MANIFEST_FIELDS = {"version", "generated_at", "pipeline_hash", "sources", "stats"}


def validate_chunks_artifact(path: Path) -> list:
    """Return a list of error strings; empty list means the artifact is valid."""
    errors = []
    if not path.exists():
        return [f"Missing artifact: {path}"]

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"Invalid JSON in {path}: {exc}"]

    missing_meta = REQUIRED_META_FIELDS - set(data.get("meta", {}).keys())
    if missing_meta:
        errors.append(f"chunks_latest.json meta missing fields: {missing_meta}")

    chunks = data.get("chunks", [])
    if not chunks:
        errors.append("chunks_latest.json has no chunks")
        return errors

    for i, chunk in enumerate(chunks):
        missing = REQUIRED_CHUNK_FIELDS - set(chunk.keys())
        if missing:
            errors.append(f"Chunk {i} (id={chunk.get('id', '?')}) missing fields: {missing}")
        for field in ("id", "hash", "source", "category"):
            if not chunk.get(field):
                errors.append(f"Chunk {i} has empty {field!r}")

    return errors


def validate_manifest(path: Path) -> list:
    """Return a list of error strings; empty list means the manifest is valid."""
    if not path.exists():
        return [f"Missing manifest: {path}"]

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"Invalid JSON in {path}: {exc}"]

    missing = REQUIRED_MANIFEST_FIELDS - set(data.keys())
    if missing:
        return [f"manifest.json missing fields: {missing}"]
    return []


def validate_all(dist_dir: Path = DIST_DIR) -> bool:
    """
    Run all validation checks against *dist_dir*.

    Returns True if all checks pass, False otherwise.
    Prints a summary line for each check.
    """
    all_errors = []
    all_errors += validate_chunks_artifact(dist_dir / "chunks_latest.json")
    all_errors += validate_manifest(dist_dir / "manifest.json")

    if all_errors:
        for err in all_errors:
            print(f"❌ {err}")
        return False

    print("✅ All validation checks passed")
    return True
