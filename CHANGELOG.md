# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-04-10

### Changed
- Formalized `base-conhecimento.json` as the canonical single-file knowledge base contract.
- Updated CI structure validation to verify the unified contract keys in `base-conhecimento.json`.
- Updated README migration guidance to remove the old two-file contract (`base_coren.json` + `programação ia.json`) as the default model.

### Removed
- Legacy CI contract assumptions for `base_coren.json` and `programação ia.json`.

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
