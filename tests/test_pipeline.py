"""
Tests for the knowledge base pipeline.

Covers each stage (ingest, normalize, chunk, version/deduplicate, publish,
validate) with unit tests plus one end-to-end smoke test against the real
source files.
"""
import json
import hashlib
import tempfile
from pathlib import Path

import pytest

from pipeline.ingest import load_source, ingest_all
from pipeline.normalize import (
    normalize_knowledge_entry,
    normalize_knowledge_base,
    normalize_source,
)
from pipeline.chunk import chunk_knowledge_entries, chunk_ia_config, _content_hash
from pipeline.version import deduplicate
from pipeline.publish import publish
from pipeline.validate import validate_chunks_artifact, validate_manifest, validate_all


# ── Shared fixtures ──────────────────────────────────────────────────────────

SAMPLE_KB_JSON = {
    "base_conhecimento": [
        {
            "categoria": "negociacao_debitos",
            "mensagem": "Quero verificar minhas anuidades.",
            "resposta": "Olá profissional.",
        },
        {
            "categoria": "DUVIDA",
            "pergunta": "Por que pago anuidade?",
            "resposta": "Porque está inscrito.",
            "palavras_chave": ["anuidade", "obrigação"],
        },
    ]
}

SAMPLE_IA_CONFIG = {
    "project": {"name": "Test Project"},
    "role": {"description": "Test role", "tone": ["empático"]},
    "knowledge_base": {"core_rules": []},
    "common_objections": [],
    "response_structure": [],
    "forbidden_behaviors": [],
}


def _write_kb(tmp_path: Path) -> Path:
    p = tmp_path / "base_coren.json"
    p.write_text(json.dumps(SAMPLE_KB_JSON), encoding="utf-8")
    return p


def _write_ia(tmp_path: Path) -> Path:
    p = tmp_path / "programação ia.json"
    p.write_text(json.dumps(SAMPLE_IA_CONFIG), encoding="utf-8")
    return p


def _make_chunks(n: int = 2) -> list:
    return [
        {
            "id": f"id{i:016x}",
            "chunk_index": i,
            "source": "base_coren.json",
            "category": f"cat{i}",
            "text": f"text {i}",
            "response": f"resp {i}",
            "keywords": [],
            "version": "1.3.0",
            "hash": hashlib.sha256(f"cat{i}|text {i}|resp {i}".encode()).hexdigest(),
        }
        for i in range(n)
    ]


def _make_ia_artifact() -> dict:
    cfg = {"project": {"name": "Test"}}
    raw = json.dumps(cfg, sort_keys=True, ensure_ascii=False)
    h = hashlib.sha256(raw.encode()).hexdigest()
    return {
        "id": h[:16],
        "source": "programação ia.json",
        "version": "1.3.0",
        "hash": h,
        "config": cfg,
    }


def _make_sources() -> list:
    return [
        {
            "filename": "base_coren.json",
            "source_hash": "abc" * 20,
            "ingested_at": "2026-04-01T00:00:00+00:00",
        }
    ]


# ── Stage 1: Ingest ──────────────────────────────────────────────────────────

class TestIngest:
    def test_load_source_sets_source_hash(self, tmp_path):
        p = _write_kb(tmp_path)
        result = load_source(p)
        assert len(result["source_hash"]) == 64  # SHA-256 hex digest

    def test_load_source_sets_ingested_at(self, tmp_path):
        p = _write_kb(tmp_path)
        result = load_source(p)
        assert result["ingested_at"]
        assert "T" in result["ingested_at"]  # ISO-8601 shape

    def test_load_source_identifies_known_source_type(self, tmp_path):
        p = _write_kb(tmp_path)
        result = load_source(p)
        assert result["source_type"] == "knowledge_base"

    def test_load_source_unknown_file_has_unknown_type(self, tmp_path):
        p = tmp_path / "other.json"
        p.write_text("{}", encoding="utf-8")
        result = load_source(p)
        assert result["source_type"] == "unknown"

    def test_source_hash_changes_when_content_changes(self, tmp_path):
        p = _write_kb(tmp_path)
        h1 = load_source(p)["source_hash"]
        p.write_text(json.dumps({"base_conhecimento": []}), encoding="utf-8")
        h2 = load_source(p)["source_hash"]
        assert h1 != h2

    def test_ingest_all_finds_both_sources(self, tmp_path):
        _write_kb(tmp_path)
        _write_ia(tmp_path)
        results = ingest_all(tmp_path)
        filenames = {r["filename"] for r in results}
        assert "base_coren.json" in filenames
        assert "programação ia.json" in filenames

    def test_ingest_all_skips_missing_files(self, tmp_path):
        _write_kb(tmp_path)
        results = ingest_all(tmp_path)
        assert len(results) == 1


# ── Stage 2: Normalize ───────────────────────────────────────────────────────

class TestNormalize:
    def test_normalize_legacy_schema_maps_mensagem_to_text(self):
        entry = {"categoria": "cat", "mensagem": "msg", "resposta": "resp"}
        result = normalize_knowledge_entry(entry)
        assert result["text"] == "msg"
        assert result["response"] == "resp"
        assert result["category"] == "cat"
        assert result["keywords"] == []

    def test_normalize_current_schema_maps_pergunta_to_text(self):
        entry = {"categoria": "CAT", "pergunta": "q?", "resposta": "a.", "palavras_chave": ["x"]}
        result = normalize_knowledge_entry(entry)
        assert result["text"] == "q?"
        assert result["keywords"] == ["x"]

    def test_normalize_category_is_lowercased(self):
        entry = {"categoria": "NEGOCIACAO", "mensagem": "m", "resposta": "r"}
        result = normalize_knowledge_entry(entry)
        assert result["category"] == "negociacao"

    def test_pergunta_takes_precedence_over_mensagem(self):
        entry = {"categoria": "c", "pergunta": "q", "mensagem": "m", "resposta": "r"}
        result = normalize_knowledge_entry(entry)
        assert result["text"] == "q"

    def test_normalize_knowledge_base_returns_correct_count(self):
        results = normalize_knowledge_base(SAMPLE_KB_JSON)
        assert len(results) == 2

    def test_normalize_source_attaches_normalized_key(self, tmp_path):
        p = _write_kb(tmp_path)
        from pipeline.ingest import load_source
        source = load_source(p)
        normalized = normalize_source(source)
        assert "normalized" in normalized
        assert len(normalized["normalized"]) == 2


# ── Stage 3: Chunk ───────────────────────────────────────────────────────────

class TestChunk:
    def test_chunk_adds_required_fields(self):
        entries = [{"text": "q", "response": "a", "category": "cat", "keywords": []}]
        chunks = chunk_knowledge_entries(entries, "test.json", "1.0.0")
        assert len(chunks) == 1
        c = chunks[0]
        for field in ("id", "chunk_index", "source", "category", "text", "response", "hash", "version"):
            assert field in c, f"missing field: {field}"

    def test_chunk_index_is_sequential(self):
        entries = [
            {"text": f"q{i}", "response": f"a{i}", "category": "cat", "keywords": []}
            for i in range(3)
        ]
        chunks = chunk_knowledge_entries(entries, "f.json", "1.0.0")
        assert [c["chunk_index"] for c in chunks] == [0, 1, 2]

    def test_content_hash_is_deterministic(self):
        assert _content_hash("text", "resp", "cat") == _content_hash("text", "resp", "cat")

    def test_different_content_gives_different_hash(self):
        assert _content_hash("text1", "resp", "cat") != _content_hash("text2", "resp", "cat")

    def test_id_is_first_16_chars_of_hash(self):
        entries = [{"text": "t", "response": "r", "category": "c", "keywords": []}]
        chunk = chunk_knowledge_entries(entries, "f.json", "1.0.0")[0]
        assert chunk["id"] == chunk["hash"][:16]

    def test_chunk_ia_config_has_hash(self):
        artifact = chunk_ia_config(SAMPLE_IA_CONFIG, "ia.json", "1.0.0")
        assert len(artifact["hash"]) == 64

    def test_chunk_ia_config_preserves_config(self):
        artifact = chunk_ia_config(SAMPLE_IA_CONFIG, "ia.json", "1.0.0")
        assert artifact["config"] == SAMPLE_IA_CONFIG


# ── Stage 4: Deduplicate ─────────────────────────────────────────────────────

class TestDeduplicate:
    def test_exact_duplicate_is_removed(self):
        chunk = {"hash": "abc123", "id": "1", "text": "t"}
        unique, removed = deduplicate([chunk, chunk])
        assert len(unique) == 1
        assert len(removed) == 1

    def test_unique_chunks_are_preserved(self):
        c1 = {"hash": "aaa", "id": "1"}
        c2 = {"hash": "bbb", "id": "2"}
        unique, removed = deduplicate([c1, c2])
        assert len(unique) == 2
        assert removed == []

    def test_empty_input_returns_empty(self):
        unique, removed = deduplicate([])
        assert unique == []
        assert removed == []

    def test_order_is_preserved_for_first_occurrence(self):
        chunks = [
            {"hash": "a", "id": "1"},
            {"hash": "b", "id": "2"},
            {"hash": "a", "id": "3"},  # duplicate of first
        ]
        unique, _ = deduplicate(chunks)
        assert [c["id"] for c in unique] == ["1", "2"]


# ── Stage 5: Publish ─────────────────────────────────────────────────────────

class TestPublish:
    def test_creates_all_three_artifacts(self, tmp_path):
        publish(_make_chunks(), _make_ia_artifact(), "1.3.0", _make_sources(), [], tmp_path)
        assert (tmp_path / "chunks_latest.json").exists()
        assert (tmp_path / "config_latest.json").exists()
        assert (tmp_path / "manifest.json").exists()

    def test_chunks_artifact_has_correct_meta(self, tmp_path):
        chunks = _make_chunks(3)
        publish(chunks, _make_ia_artifact(), "1.3.0", _make_sources(), [], tmp_path)
        data = json.loads((tmp_path / "chunks_latest.json").read_text())
        assert data["meta"]["total_chunks"] == 3
        assert data["meta"]["version"] == "1.3.0"
        assert data["meta"]["schema_version"] == "1.0"

    def test_manifest_dedup_stats(self, tmp_path):
        publish(_make_chunks(), _make_ia_artifact(), "1.3.0", _make_sources(), ["h1", "h2"], tmp_path)
        manifest = json.loads((tmp_path / "manifest.json").read_text())
        assert manifest["stats"]["deduplicated"] == 2

    def test_pipeline_hash_is_stable_for_same_input(self, tmp_path):
        chunks = _make_chunks()
        ia = _make_ia_artifact()
        m1 = publish(chunks, ia, "1.3.0", _make_sources(), [], tmp_path)
        m2 = publish(chunks, ia, "1.3.0", _make_sources(), [], tmp_path)
        assert m1["pipeline_hash"] == m2["pipeline_hash"]

    def test_pipeline_hash_changes_when_chunks_change(self, tmp_path):
        ia = _make_ia_artifact()
        m1 = publish(_make_chunks(2), ia, "1.3.0", _make_sources(), [], tmp_path)
        m2 = publish(_make_chunks(3), ia, "1.3.0", _make_sources(), [], tmp_path)
        assert m1["pipeline_hash"] != m2["pipeline_hash"]


# ── Stage 6: Validate ────────────────────────────────────────────────────────

class TestValidate:
    def test_passes_after_successful_publish(self, tmp_path):
        publish(_make_chunks(), _make_ia_artifact(), "1.3.0", _make_sources(), [], tmp_path)
        assert validate_all(tmp_path) is True

    def test_fails_when_artifact_missing(self, tmp_path):
        errors = validate_chunks_artifact(tmp_path / "chunks_latest.json")
        assert errors

    def test_fails_when_manifest_missing(self, tmp_path):
        errors = validate_manifest(tmp_path / "manifest.json")
        assert errors

    def test_detects_missing_chunk_field(self, tmp_path):
        chunks = _make_chunks(1)
        del chunks[0]["hash"]  # remove required field
        publish(chunks, _make_ia_artifact(), "1.3.0", _make_sources(), [], tmp_path)
        errors = validate_chunks_artifact(tmp_path / "chunks_latest.json")
        assert any("hash" in e for e in errors)

    def test_detects_empty_chunk_list(self, tmp_path):
        publish([], _make_ia_artifact(), "1.3.0", _make_sources(), [], tmp_path)
        errors = validate_chunks_artifact(tmp_path / "chunks_latest.json")
        assert any("no chunks" in e.lower() for e in errors)


# ── End-to-end ───────────────────────────────────────────────────────────────

class TestEndToEnd:
    def test_full_pipeline_against_real_sources(self, tmp_path):
        """Smoke test: run the complete pipeline using the real source files."""
        from pipeline.run_pipeline import run

        repo_root = Path(__file__).parent.parent
        ok = run(root=repo_root, dist=tmp_path)
        assert ok, "Pipeline returned failure"

    def test_real_chunks_have_required_metadata(self, tmp_path):
        from pipeline.run_pipeline import run

        repo_root = Path(__file__).parent.parent
        run(root=repo_root, dist=tmp_path)
        data = json.loads((tmp_path / "chunks_latest.json").read_text())
        assert data["meta"]["total_chunks"] > 0
        for chunk in data["chunks"]:
            for field in ("id", "hash", "source", "category", "text", "response", "version"):
                assert chunk.get(field), f"Chunk missing or empty field: {field!r}"

    def test_real_pipeline_has_no_duplicates(self, tmp_path):
        from pipeline.run_pipeline import run

        repo_root = Path(__file__).parent.parent
        run(root=repo_root, dist=tmp_path)
        data = json.loads((tmp_path / "chunks_latest.json").read_text())
        hashes = [c["hash"] for c in data["chunks"]]
        assert len(hashes) == len(set(hashes)), "Duplicate hashes found in output"
