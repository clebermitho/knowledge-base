"""
Normalize stage: unifies the two divergent schemas present in base_coren.json
into a single canonical shape, and passes ia_config through unchanged.

Trade-off: base_coren.json contains two internal schemas that accumulated over
time:
  - Legacy  (first 12 items): {categoria, mensagem, resposta}
  - Current (remaining items): {pergunta, resposta, categoria, palavras_chave}

Rather than migrating the source file (which would break callers that still
read it directly), this stage performs the unification at pipeline runtime.
The canonical shape is:

  {
    "text":     str,   # the incoming message / question
    "response": str,   # the suggested reply
    "category": str,   # topic label (normalised to lower-case)
    "keywords": list   # optional keyword hints for retrieval
  }

ia_config is returned as-is because its structure is intentional and consumed
as a whole block by the backend prompt-construction layer.
"""


def _normalise_category(raw: str) -> str:
    """Lower-case and strip whitespace for consistent category keys."""
    return raw.strip().lower() if raw else ""


def normalize_knowledge_entry(entry: dict) -> dict:
    """Normalize a single knowledge-base entry to the canonical schema."""
    # 'pergunta' (current schema) takes precedence over 'mensagem' (legacy)
    text = entry.get("pergunta") or entry.get("mensagem", "")
    return {
        "text": text,
        "response": entry.get("resposta", ""),
        "category": _normalise_category(entry.get("categoria", "")),
        "keywords": entry.get("palavras_chave", []),
    }


def normalize_knowledge_base(data: dict) -> list:
    """Normalise all entries inside the base_conhecimento array."""
    entries = data.get("base_conhecimento", [])
    return [normalize_knowledge_entry(e) for e in entries]


def normalize_ia_config(data: dict) -> dict:
    """Return ia_config unchanged; its nested structure is consumed as-is."""
    return data


def normalize_source(source: dict) -> dict:
    """Attach a 'normalized' key to a source record produced by ingest."""
    source_type = source["source_type"]
    if source_type == "knowledge_base":
        normalized = normalize_knowledge_base(source["data"])
    elif source_type == "ia_config":
        normalized = normalize_ia_config(source["data"])
    else:
        normalized = source["data"]
    return {**source, "normalized": normalized}
