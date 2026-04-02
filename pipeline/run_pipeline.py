#!/usr/bin/env python3
"""
Knowledge Base Pipeline — orchestrator

Executes all pipeline stages in sequence:
  ingest → normalize → chunk → deduplicate → publish → validate

Usage:
    python -m pipeline.run_pipeline
    python -m pipeline.run_pipeline --root /path/to/repo --dist /path/to/output
"""
import sys
import argparse
from pathlib import Path

from pipeline.ingest import ingest_all
from pipeline.normalize import normalize_source
from pipeline.chunk import chunk_knowledge_entries, chunk_ia_config
from pipeline.version import deduplicate
from pipeline.publish import publish, DIST_DIR
from pipeline.validate import validate_all


def _read_version(root: Path) -> str:
    version_file = root / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.0.0"


def run(root: Path = Path("."), dist: Path = DIST_DIR) -> bool:
    """
    Execute the full pipeline.

    Parameters
    ----------
    root: repository root (source JSON files are expected here)
    dist: output directory for published artifacts

    Returns True on success, False if validation fails.
    """
    version = _read_version(root)
    print(f"🔄 Starting pipeline — version {version}")

    # Stage 1: Ingest
    sources = ingest_all(root)
    if not sources:
        print("❌ No source files found — aborting")
        return False
    print(f"📥 Ingested {len(sources)} source(s): {[s['filename'] for s in sources]}")

    # Stage 2: Normalise
    normalized = [normalize_source(s) for s in sources]

    # Stage 3: Chunk
    all_chunks: list = []
    ia_config_artifact = None

    for source in normalized:
        if source["source_type"] == "knowledge_base":
            chunks = chunk_knowledge_entries(
                source["normalized"], source["filename"], version
            )
            all_chunks.extend(chunks)
            print(f"   🔪 {source['filename']} → {len(chunks)} chunk(s)")
        elif source["source_type"] == "ia_config":
            ia_config_artifact = chunk_ia_config(
                source["normalized"], source["filename"], version
            )
            print(f"   🔧 {source['filename']} → ia_config artifact")

    if ia_config_artifact is None:
        print("❌ ia_config source not found — aborting")
        return False

    # Stage 4: Deduplicate
    unique_chunks, removed = deduplicate(all_chunks)
    if removed:
        print(f"♻️  Removed {len(removed)} duplicate(s)")
    print(f"✅ {len(unique_chunks)} unique chunk(s) after deduplication")

    # Stage 5: Publish
    manifest = publish(unique_chunks, ia_config_artifact, version, sources, removed, dist)
    print(f"📦 Artifacts written to {dist}/")
    print(f"   pipeline_hash: {manifest['pipeline_hash'][:16]}…")

    # Stage 6: Validate
    ok = validate_all(dist)
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Knowledge Base Pipeline")
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root directory (default: current directory)",
    )
    parser.add_argument(
        "--dist",
        default=str(DIST_DIR),
        help="Output directory for artifacts (default: dist/)",
    )
    args = parser.parse_args()
    ok = run(Path(args.root), Path(args.dist))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
