"""
Version stage: deduplicates chunks and manages version metadata.

Deduplication strategy
  Chunks are deduplicated by their full content hash (SHA-256 of
  category|text|response).  Two entries that share identical content will
  produce the same hash and be collapsed to one chunk.

Trade-off: hash-based deduplication catches exact text duplicates only.
Semantically equivalent entries with different wording are NOT merged.
Perfect semantic deduplication would require embedding comparison and is
out of scope for this foundation phase.  The current approach is O(n) and
deterministic, which is sufficient for the dataset size.

The function returns both the deduplicated list and the list of removed hashes
so that the publish stage can surface deduplication stats in the manifest.
"""


def deduplicate(chunks: list) -> tuple:
    """
    Remove duplicate chunks based on content hash.

    Returns:
        (unique_chunks, removed_hashes)
    """
    seen: set = set()
    unique: list = []
    removed: list = []
    for chunk in chunks:
        h = chunk.get("hash", "")
        if h in seen:
            removed.append(h)
        else:
            seen.add(h)
            unique.append(chunk)
    return unique, removed
