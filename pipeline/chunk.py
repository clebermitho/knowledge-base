"""
Chunk stage: converts normalised entries into discrete, addressable chunks.

Design decision — granularity
  Each Q&A pair is the natural unit of retrieval in this knowledge base:
  messages are short (1-3 sentences) and the answer is tightly coupled to the
  question.  Splitting further would fragment context without improving recall.
  Revisit if average entry length grows beyond ~300 tokens.

Each chunk carries the full set of traceability metadata required by the
backend for RAG indexing:

  id           – first 16 hex chars of content_hash (stable, URL-safe)
  chunk_index  – position within the source file (for ordered reconstruction)
  source       – originating filename
  category     – normalised topic label
  text         – the incoming message / question
  response     – the suggested reply
  keywords     – optional retrieval hints
  version      – pipeline version at generation time
  hash         – full SHA-256 of (category|text|response) for deduplication

Trade-off: the hash covers content only, not metadata (version, source).
This means re-ingesting the same text from a renamed file does NOT produce
a duplicate — intentional, because content is the truth, not location.
"""
import hashlib
import json


def _content_hash(text: str, response: str, category: str) -> str:
    """Deterministic SHA-256 over the three content fields."""
    payload = f"{category}|{text}|{response}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def chunk_knowledge_entries(entries: list, source_filename: str, version: str) -> list:
    """Convert a list of normalised knowledge entries into chunk dicts."""
    chunks = []
    for idx, entry in enumerate(entries):
        content_hash = _content_hash(entry["text"], entry["response"], entry["category"])
        chunks.append({
            "id": content_hash[:16],
            "chunk_index": idx,
            "source": source_filename,
            "category": entry["category"],
            "text": entry["text"],
            "response": entry["response"],
            "keywords": entry["keywords"],
            "version": version,
            "hash": content_hash,
        })
    return chunks


def chunk_ia_config(config: dict, source_filename: str, version: str) -> dict:
    """Wrap the ia_config dict as a single versioned artifact with a content hash."""
    raw = json.dumps(config, sort_keys=True, ensure_ascii=False)
    config_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return {
        "id": config_hash[:16],
        "source": source_filename,
        "version": version,
        "hash": config_hash,
        "config": config,
    }
