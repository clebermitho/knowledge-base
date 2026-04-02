"""
Publish stage: writes stable, versioned artifacts to the dist/ directory.

Backend contract
  The backend (clebermitho/Backend-correto) should consume:
    - dist/chunks_latest.json   Knowledge Q&A chunks for RAG context retrieval
    - dist/config_latest.json   IA system configuration for prompt construction
    - dist/manifest.json        Pipeline run manifest for cache invalidation

  Cache invalidation: compare manifest.pipeline_hash.  If it differs from the
  previously cached value, re-fetch chunks_latest.json and/or config_latest.json.

Artifact schema version
  All artifacts carry a schema_version field.  Increment it (not pipeline
  version) when the artifact shape changes in a breaking way.

Migration note
  The raw source files (base_coren.json, programação ia.json) remain in place
  for backward compatibility.  Consumers should migrate to dist/ artifacts.
  Raw source files will be deprecated once all consumers use the dist/ outputs.
"""
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path


DIST_DIR = Path("dist")


def _pipeline_hash(chunks: list, config_hash: str) -> str:
    """Stable hash covering the full set of chunk hashes + ia_config hash."""
    chunk_hashes = "".join(c.get("hash", "") for c in chunks)
    return hashlib.sha256(f"{chunk_hashes}{config_hash}".encode("utf-8")).hexdigest()


def publish(
    chunks: list,
    ia_config_artifact: dict,
    version: str,
    sources: list,
    removed_hashes: list,
    dist_dir: Path = DIST_DIR,
) -> dict:
    """
    Write artifacts to *dist_dir* and return the manifest dict.

    Parameters
    ----------
    chunks:             deduplicated knowledge chunks
    ia_config_artifact: versioned ia_config wrapper produced by chunk stage
    version:            pipeline version string (from VERSION file)
    sources:            ingest source records (for provenance in manifest)
    removed_hashes:     hashes dropped by deduplication
    dist_dir:           output directory (default: dist/)
    """
    dist_dir.mkdir(exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat()
    pipeline_hash = _pipeline_hash(chunks, ia_config_artifact["hash"])

    chunks_artifact = {
        "meta": {
            "version": version,
            "generated_at": generated_at,
            "total_chunks": len(chunks),
            "sources": [s["filename"] for s in sources],
            "pipeline_hash": pipeline_hash,
            "schema_version": "1.0",
        },
        "chunks": chunks,
    }

    config_artifact = {
        "meta": {
            "version": version,
            "generated_at": generated_at,
            "source": ia_config_artifact["source"],
            "hash": ia_config_artifact["hash"],
            "schema_version": "1.0",
        },
        "config": ia_config_artifact["config"],
    }

    manifest = {
        "version": version,
        "generated_at": generated_at,
        "pipeline_hash": pipeline_hash,
        "sources": [
            {
                "filename": s["filename"],
                "source_hash": s["source_hash"],
                "ingested_at": s["ingested_at"],
            }
            for s in sources
        ],
        "stats": {
            "total_chunks": len(chunks),
            "deduplicated": len(removed_hashes),
        },
        "artifacts": ["chunks_latest.json", "config_latest.json"],
    }

    (dist_dir / "chunks_latest.json").write_text(
        json.dumps(chunks_artifact, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (dist_dir / "config_latest.json").write_text(
        json.dumps(config_artifact, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (dist_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return manifest
