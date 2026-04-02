# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-04-02

### Added
- `pipeline/` package implementing the full knowledge pipeline:
  - `ingest.py` — loads sources, computes `source_hash`, records `ingested_at`
  - `normalize.py` — unifies legacy `{mensagem}` and current `{pergunta}` schemas into a canonical shape; lower-cases categories
  - `chunk.py` — converts each normalised entry into an addressable chunk with `id`, `hash`, `version`, `source`, `category`, `keywords`
  - `version.py` — exact-match deduplication by SHA-256 content hash
  - `publish.py` — writes `dist/chunks_latest.json`, `dist/config_latest.json`, `dist/manifest.json`
  - `validate.py` — structural quality gate (required fields, non-empty ids/hashes)
  - `run_pipeline.py` — CLI orchestrator; exits non-zero on validation failure
- `tests/test_pipeline.py` — 37 unit + end-to-end tests covering all pipeline stages
- `dist/chunks_latest.json` — 27 knowledge chunks with full traceability metadata
- `dist/config_latest.json` — versioned ia_config artifact for prompt construction
- `dist/manifest.json` — pipeline run manifest for cache invalidation
- Updated CI workflow to run Python tests and the pipeline on every push/PR

### Changed
- README rewritten with pipeline architecture, artifact format, how-to-run and contribution guide
- VERSION bumped to 1.3.0
- CI extended with Python 3.12 setup, `pytest` run and pipeline validation step

### Technical decisions and trade-offs
- **Chunking granularity**: each Q&A pair is one chunk (no sub-sentence splitting).
  Entries are 1–5 sentences; further splitting would fragment context without improving recall.
  Revisit if average entry length exceeds ~300 tokens.
- **Deduplication**: exact hash match only. Semantic deduplication requires embeddings
  and is deferred to the RAG indexing layer in the backend.
- **Source files preserved**: `base_coren.json` and `programação ia.json` remain unchanged
  for backward compatibility. Consumers should migrate to `dist/` artifacts.
- **No new runtime dependencies**: pipeline uses Python stdlib only (hashlib, json, pathlib,
  datetime). pytest is the only new dev dependency.

## [1.2.0] - 2026-03-29

### Added
- Complete README.md documentation (file structure, categories, IA config, contribution guide)
- CI/CD pipeline with GitHub Actions (JSON validation, structure check, VERSION check)
- VERSION file for unified ecosystem versioning
- CHANGELOG.md

### Changed
- Rewrote README.md from placeholder to full documentation

## Previous

### Notes
- Initial repository with base_coren.json and programação ia.json
- Knowledge base for Chatplay Assistant IA
