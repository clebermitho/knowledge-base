# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-04-02

### Added
- `docs/fase-0-diagnostico.md`: Diagnóstico técnico completo (as-is) — inventário de artefatos, problemas identificados, baseline de qualidade, contratos existentes e lacunas
- `docs/fase-1-arquitetura-alvo.md`: Arquitetura alvo (to-be) — pipeline de ingestão→limpeza→validação→versionamento→publicação, metadados mínimos, boundary KB/backend/clientes, plano de migração
- `schemas/kb-entry.schema.json`: JSON Schema formal para validação de entradas da base de conhecimento
- `ia_config.json`: Nome canônico do arquivo de configuração da IA (sem espaço/acento; `programação ia.json` mantido por compatibilidade)

### Changed
- `base_coren.json`: Schema normalizado para v1.3.0 — campo canônico `pergunta` (unifica `mensagem`/`pergunta`), `palavras_chave` em todas as entradas, metadados obrigatórios (`id`, `hash`, `versao`, `origem`, `criado_em`, `atualizado_em`, `ativo`), categorias normalizadas para snake_case, 2 duplicatas diretas removidas (24 → 22 entradas únicas)
- `.github/workflows/ci.yml`: Validação expandida — verifica campos obrigatórios por entrada, detecta IDs duplicados, detecta hashes duplicados (possível duplicação de conteúdo), suporta tanto `ia_config.json` quanto `programação ia.json`
- `README.md`: Atualizado para refletir nova estrutura, schema v1.3.0, boundary arquitetural e instruções de contribuição

### Deprecated
- `programação ia.json`: Use `ia_config.json` em novos scripts e automações



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
