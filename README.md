# 📚 Chatplay Knowledge Base

Base de conhecimento centralizada para o assistente IA do **Chatplay Assistant** — plataforma de atendimento inteligente para profissionais de enfermagem (Coren/Cofen).

O repositório expõe um **pipeline de conhecimento** que ingere, normaliza, chunka, versiona e publica artefatos prontos para consumo pelo backend (RAG, busca semântica, construção de prompt).

---

## 🏗️ Arquitetura do Pipeline

```
Fontes (JSON)
    │
    ▼
[1] ingest      – carrega arquivos, calcula source_hash, registra ingested_at
    │
    ▼
[2] normalize   – unifica schemas divergentes num esquema canônico
    │
    ▼
[3] chunk       – converte cada entrada numa unidade endereçável com metadados
    │
    ▼
[4] deduplicate – remove duplicatas exatas por hash de conteúdo (SHA-256)
    │
    ▼
[5] publish     – escreve artefatos estáveis em dist/
    │
    ▼
[6] validate    – verifica presença de metadados obrigatórios e consistência
```

### Módulos (`pipeline/`)

| Módulo | Responsabilidade |
|--------|-----------------|
| `ingest.py` | Lê fontes JSON, calcula `source_hash`, registra `ingested_at` |
| `normalize.py` | Unifica os dois schemas de `base_coren.json` em esquema canônico |
| `chunk.py` | Cria chunks com `id`, `hash`, `version`, `category`, `source`, etc. |
| `version.py` | Deduplicação por hash de conteúdo; retorna removidos para o manifesto |
| `publish.py` | Escreve `dist/chunks_latest.json`, `dist/config_latest.json`, `dist/manifest.json` |
| `validate.py` | Verificações estruturais obrigatórias; falha com código não-zero |
| `run_pipeline.py` | Orquestrador CLI que encadeia todos os estágios |

---

## 📦 Artefatos Publicados (`dist/`)

### `dist/chunks_latest.json`
Chunks de conhecimento para RAG/indexação semântica.

```json
{
  "meta": {
    "version": "1.3.0",
    "generated_at": "2026-04-02T21:00:00+00:00",
    "total_chunks": 27,
    "sources": ["base_coren.json"],
    "pipeline_hash": "bc11b699...",
    "schema_version": "1.0"
  },
  "chunks": [
    {
      "id": "a1b2c3d4e5f60001",
      "chunk_index": 0,
      "source": "base_coren.json",
      "category": "negociacao_debitos",
      "text": "Quero verificar minhas anuidades.",
      "response": "Olá profissional...",
      "keywords": [],
      "version": "1.3.0",
      "hash": "sha256..."
    }
  ]
}
```

### `dist/config_latest.json`
Configuração da IA (tom, regras, objeções, estrutura de resposta) para construção de prompt.

### `dist/manifest.json`
Manifesto do pipeline para invalidação de cache e rastreabilidade.

```json
{
  "version": "1.3.0",
  "generated_at": "...",
  "pipeline_hash": "bc11b699...",
  "sources": [{ "filename": "...", "source_hash": "...", "ingested_at": "..." }],
  "stats": { "total_chunks": 27, "deduplicated": 0 },
  "artifacts": ["chunks_latest.json", "config_latest.json"]
}
```

**Invalidação de cache no backend**: compare `manifest.pipeline_hash` com o valor em cache. Se diferir, re-busque `chunks_latest.json` e/ou `config_latest.json`.

---

## ▶️ Como Rodar

### Pré-requisitos
- Python 3.10+

### Executar o pipeline
```bash
python -m pipeline.run_pipeline
# Saída em dist/ (chunks_latest.json, config_latest.json, manifest.json)
```

Opções:
```bash
python -m pipeline.run_pipeline --root /caminho/do/repo --dist /caminho/de/saida
```

### Executar os testes
```bash
pip install pytest
python -m pytest tests/ -v
```

### Validar artefatos gerados
```bash
python -c "from pipeline.validate import validate_all; exit(0 if validate_all() else 1)"
```

---

## 📁 Estrutura de Arquivos

```
knowledge-base/
├── base_coren.json          # Fonte: Q&A de atendimento Coren/Cofen
├── programação ia.json      # Fonte: configuração do comportamento da IA
├── VERSION                  # Versão atual do pipeline
├── pipeline/
│   ├── ingest.py
│   ├── normalize.py
│   ├── chunk.py
│   ├── version.py
│   ├── publish.py
│   ├── validate.py
│   └── run_pipeline.py
├── tests/
│   └── test_pipeline.py
└── dist/                    # Artefatos publicados (gerados pelo pipeline)
    ├── chunks_latest.json
    ├── config_latest.json
    └── manifest.json
```

---

## 🏷️ Categorias da Base Coren

| Categoria | Descrição |
|-----------|-----------|
| `negociacao_debitos` | Verificação e negociação de anuidades |
| `duvida_anuidade` | Explicação sobre obrigatoriedade da anuidade |
| `prazo_pagamento` | Solicitações de prazo para pagamento |
| `suspensao_registro` | Orientação sobre suspensão de inscrição |
| `cancelamento_registro` | Orientação sobre cancelamento de inscrição |
| `ja_suspendeu` / `ja_cancelou` | Acompanhamento pós-solicitação |
| `nada_consta` | Emissão de certidão Nada Consta |
| `nao_trabalho_area` | Profissionais que não atuam mais |
| `sem_dinheiro` | Situações de dificuldade financeira |
| `entrada_acordo` | Dúvidas sobre entrada em acordos |
| `golpe_duvida` | Validação de legitimidade do contato |

---

## 🔧 Como Contribuir

1. Adicione ou edite entradas em `base_coren.json` usando o formato:
   ```json
   {
     "categoria": "NOME_DA_CATEGORIA",
     "pergunta": "texto da pergunta",
     "resposta": "texto da resposta",
     "palavras_chave": ["palavra1", "palavra2"]
   }
   ```
2. Execute o pipeline: `python -m pipeline.run_pipeline`
3. Execute os testes: `python -m pytest tests/ -v`
4. Valide os artefatos: `python -c "from pipeline.validate import validate_all; exit(0 if validate_all() else 1)"`
5. Abra um Pull Request — o CI executa tudo automaticamente.

---

## 🔗 Repositórios Relacionados

| Repositório | Função |
|-------------|--------|
| [Backend-correto](https://github.com/clebermitho/Backend-correto) | API central (Express + Prisma) — auth, eventos, métricas, proxy OpenAI |
| [Admin-Assistant-Chat](https://github.com/clebermitho/Admin-Assistant-Chat) | Painel administrativo (React + TypeScript + Vite) |
| [Arquivos-para-IA](https://github.com/clebermitho/Arquivos-para-IA) | Extensão Chrome (Manifest V3) |

**Contrato com o Backend**: o backend consome `dist/chunks_latest.json` para RAG e `dist/config_latest.json` para construção de prompt. Os arquivos fonte legados (`base_coren.json`, `programação ia.json`) são mantidos para compatibilidade retroativa.

---

## 📋 Versionamento

- **Versão do ecossistema**: Consulte o arquivo `VERSION`
- Todos os repositórios seguem [Semantic Versioning](https://semver.org/)
- O campo `pipeline_hash` em `dist/manifest.json` identifica unicamente o estado dos artefatos publicados.
