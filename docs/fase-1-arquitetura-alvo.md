# Fase 1 — Arquitetura Alvo: Knowledge Base

**Repositório:** `clebermitho/knowledge-base`
**Data:** 2026-04-02
**Versão alvo:** 1.3.0+
**Autor:** Copilot — Programa de Modernização (Fase 0/Fase 1)

---

## 1. Visão Geral da Arquitetura Alvo

O objetivo desta fase é transformar o `knowledge-base` de um repositório de arquivos JSON brutos consumidos diretamente pelo cliente em uma **fonte de verdade versionada, estruturada e servível via backend**, desacoplada de qualquer cliente.

### Princípios arquiteturais

1. **Desacoplamento**: o `knowledge-base` não sabe quem o consome — ele apenas produz.
2. **Pipeline explícito**: toda mudança no conteúdo passa por ingestão → limpeza → validação → versionamento → publicação.
3. **Metadados obrigatórios**: nenhuma entrada entra na base sem `id`, `hash`, `versao`, `criado_em`, `atualizado_em` e `origem`.
4. **Atualização incremental**: consumidores recebem apenas o que mudou, não a base completa.
5. **Observabilidade**: cada etapa do pipeline é rastreável e auditável.

---

## 2. Pipeline Alvo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         KNOWLEDGE BASE PIPELINE                             │
│                                                                             │
│  Fontes de Conteúdo                                                         │
│  ──────────────────                                                         │
│  [Manual PR] ──┐                                                            │
│  [Admin UI]  ──┼──▶  [ INGESTÃO ]                                          │
│  [Import CSV]──┘       │                                                    │
│                        │  • Leitura dos arquivos fonte                      │
│                        │  • Conversão para schema canônico                  │
│                        │  • Atribuição de ID único (UUID v5/hash)           │
│                        ▼                                                    │
│                   [ LIMPEZA ]                                               │
│                        │  • Normalização de texto (trim, lowercase para KB) │
│                        │  • Remoção de HTML/markdown desnecessário          │
│                        │  • Validação de campos obrigatórios                │
│                        ▼                                                    │
│                   [ VALIDAÇÃO ]                                             │
│                        │  • Verificação contra JSON Schema                  │
│                        │  • Detecção de duplicatas (hash de conteúdo)       │
│                        │  • Validação de categoria (enum fixo)              │
│                        │  • Verificação de completude (sem campos vazios)   │
│                        ▼                                                    │
│                   [ CHUNKING ]  (Fase futura — RAG)                        │
│                        │  • Segmentação de respostas longas                 │
│                        │  • Geração de embeddings (OpenAI/local)            │
│                        │  • Indexação vetorial (pgvector / Pinecone)        │
│                        ▼                                                    │
│                   [ VERSIONAMENTO ]                                         │
│                        │  • Hash SHA-256 do conteúdo normalizado            │
│                        │  • Incremento de versão semântica do artefato      │
│                        │  • Registro de diff (entradas adicionadas/         │
│                        │    removidas/alteradas)                            │
│                        ▼                                                    │
│                   [ PUBLICAÇÃO ]                                            │
│                        │  • Geração de artefato versionado                  │
│                        │    (ex: kb-coren-v1.3.0.json)                      │
│                        │  • Geração de índice incremental                   │
│                        │    (ex: kb-coren-delta-v1.2.0-v1.3.0.json)        │
│                        │  • Geração de manifesto de versões                 │
│                        ▼                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │              ARTEFATOS PUBLICADOS (outputs)                      │        │
│  │  • dist/kb-coren-latest.json      ← snapshot completo atual     │        │
│  │  • dist/kb-coren-v{X.Y.Z}.json    ← snapshot por versão         │        │
│  │  • dist/kb-delta-{from}-{to}.json ← diff incremental            │        │
│  │  • dist/manifest.json             ← índice de versões           │        │
│  └─────────────────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Fluxo: knowledge-base → Backend → Clientes

```
┌─────────────────┐     ┌──────────────────────────────────────────────────┐
│  knowledge-base │     │                   Backend                        │
│  (este repo)    │     │  ┌────────────────────────────────────────────┐  │
│                 │     │  │  KB Sync Service                           │  │
│  dist/          │────▶│  │  • Polling periódico ou webhook            │  │
│  kb-latest.json │     │  │  • Consume manifest.json                   │  │
│  manifest.json  │     │  │  • Aplica delta incremental                │  │
│                 │     │  │  • Persiste em DB (PostgreSQL + pgvector)  │  │
└─────────────────┘     │  └────────────────────────────────────────────┘  │
                        │                   │                               │
                        │                   ▼                               │
                        │  ┌────────────────────────────────────────────┐  │
                        │  │  KB Query API (/v1/knowledge)              │  │
                        │  │  GET /v1/knowledge/search?q=...            │  │
                        │  │  GET /v1/knowledge/categories              │  │
                        │  │  GET /v1/knowledge/{id}                    │  │
                        │  │  GET /v1/knowledge/version                 │  │
                        │  └────────────────────────────────────────────┘  │
                        └──────────────────────────────────────────────────┘
                                      │              │
                         ┌────────────┘              └────────────┐
                         ▼                                        ▼
               ┌─────────────────┐                    ┌──────────────────┐
               │  Extensão       │                    │  Admin Panel     │
               │  (thin client)  │                    │                  │
               │  • busca sob    │                    │  • gestão de     │
               │    demanda      │                    │    entradas      │
               │  • cache TTL    │                    │  • status sync   │
               │  • sem JSON     │                    │  • auditoria     │
               │    completo     │                    │                  │
               └─────────────────┘                    └──────────────────┘
```

---

## 4. Metadados Mínimos por Entrada

Cada entrada (`KBEntry`) na base de conhecimento normalizada **deve** conter:

```typescript
interface KBEntry {
  // Identidade
  id: string;                  // UUID v5 baseado em (categoria + pergunta normalizada)
                               // ex: "kb_coren_001" ou UUID "3f5a8b..."
  
  // Conteúdo
  categoria: KBCategory;       // enum validado (ver seção 5)
  pergunta: string;            // gatilho/pergunta do cliente (normalizado)
  resposta: string;            // resposta orientativa completa
  palavras_chave: string[];    // termos para busca por palavra-chave
  
  // Metadados obrigatórios
  metadata: {
    versao: string;            // versão da entrada (semver: "1.0.0", "1.1.0", ...)
    hash: string;              // SHA-256 de (categoria+pergunta+resposta normalizados)
    origem: string;            // fonte: "manual_coren_pi", "import_csv", "admin_ui"
    criado_em: string;         // ISO 8601: "2026-03-29T00:00:00Z"
    atualizado_em: string;     // ISO 8601: última modificação
    ativo: boolean;            // soft delete: false = entrada desativada sem remoção
    tags?: string[];           // tags opcionais para agrupamento/filtragem
  };
}
```

### Enum de categorias válidas

```typescript
type KBCategory =
  | "negociacao_debitos"
  | "duvida_anuidade"
  | "prazo_pagamento"
  | "suspensao_registro"
  | "cancelamento_registro"
  | "ja_suspendeu"
  | "ja_cancelou"
  | "nada_consta"
  | "nao_trabalho_area"
  | "sem_dinheiro"
  | "entrada_acordo"
  | "golpe_duvida"
  | "consequencias_debito"
  | "desempregado"
  | "nao_vai_pagar"
  | "nao_sabia_debito"
  | "vantagens_regularizacao"
  | "endereco_coren"
  | "outros";
```

---

## 5. Estratégia de Atualização Incremental e Deduplicação

### 5.1 Detecção de Duplicatas

Algoritmo de deduplicação baseado em **hash de conteúdo normalizado**:

```
hash = SHA-256(
  lowercase(trim(categoria)) +
  lowercase(trim(normalizar_unicode(pergunta))) +
  lowercase(trim(normalizar_unicode(resposta)))
)
```

- Antes de inserir qualquer entrada, o hash é calculado e comparado com hashes existentes.
- Se hash já existe: entrada considerada duplicata — bloqueada com erro.
- Se pergunta/categoria similar (similaridade coseno > 0.92): entrada sinalizada como possível duplicata para revisão humana.

### 5.2 Atualização Incremental

**Manifesto de versões** (`dist/manifest.json`):
```json
{
  "versao_atual": "1.3.0",
  "publicado_em": "2026-04-02T20:00:00Z",
  "total_entradas": 22,
  "entradas_ativas": 22,
  "hash_snapshot": "sha256:abc123...",
  "versoes": [
    {
      "versao": "1.3.0",
      "publicado_em": "2026-04-02T20:00:00Z",
      "delta_url": "dist/kb-delta-v1.2.0-v1.3.0.json",
      "snapshot_url": "dist/kb-coren-v1.3.0.json"
    }
  ]
}
```

**Delta incremental** (`dist/kb-delta-v{from}-v{to}.json`):
```json
{
  "de": "1.2.0",
  "para": "1.3.0",
  "gerado_em": "2026-04-02T20:00:00Z",
  "adicionadas": [ ... ],
  "removidas": [ ... ],
  "alteradas": [
    {
      "id": "kb_coren_001",
      "campos_alterados": ["resposta"],
      "hash_anterior": "sha256:old...",
      "hash_novo": "sha256:new..."
    }
  ]
}
```

O backend consome o manifesto para detectar se há nova versão e aplica apenas o delta, sem recarregar a base completa.

---

## 6. Boundary: knowledge-base vs Backend vs Clientes

### 6.1 O que o `knowledge-base` entrega

| Entrega | Formato | Destino |
|---|---|---|
| Snapshot completo da KB | `dist/kb-coren-latest.json` | Backend (sync inicial) |
| Snapshot versionado | `dist/kb-coren-v{X.Y.Z}.json` | Backend (histórico/rollback) |
| Delta incremental | `dist/kb-delta-{from}-{to}.json` | Backend (sync incremental) |
| Manifesto de versões | `dist/manifest.json` | Backend (detecção de atualização) |
| Schema JSON Schema | `schemas/kb-entry.schema.json` | Backend, CI, validadores |
| Configuração da IA | `ia_config.json` | Backend (injeção de comportamento) |

### 6.2 O que o `knowledge-base` NÃO faz

- ❌ Não serve HTTP diretamente (sem servidor web)
- ❌ Não mantém banco de dados
- ❌ Não tem lógica de negócio
- ❌ Não se comunica com a extensão ou admin diretamente
- ❌ Não armazena dados de usuários ou sessões

### 6.3 O que o Backend consome e expõe

| Operação | Endpoint | Consumidor |
|---|---|---|
| Busca por texto/intenção | `GET /v1/knowledge/search?q=` | Extensão, IA |
| Busca por categoria | `GET /v1/knowledge/search?categoria=` | Extensão, IA |
| Detalhe de entrada | `GET /v1/knowledge/{id}` | Admin, IA |
| Lista de categorias | `GET /v1/knowledge/categories` | Admin, Extensão |
| Versão atual da KB | `GET /v1/knowledge/version` | Extensão (cache TTL) |
| Status de sincronização | `GET /v1/knowledge/sync/status` | Admin |

### 6.4 O que os Clientes fazem

| Cliente | Responsabilidade |
|---|---|
| **Extensão** | Busca sob demanda via API; cache local com TTL curto (ex: 5 min); sem JSON completo localmente |
| **Admin** | Gestão CRUD de entradas via API do backend; visualização de status de sync |
| **IA/LLM** | Recebe contexto filtrado e relevante via busca semântica; nunca recebe a base completa como contexto |

---

## 7. Plano de Migração / Compatibilidade

### 7.1 Breaking Changes Identificados

| Mudança | Impacto | Estratégia |
|---|---|---|
| Campo `mensagem` → `pergunta` | Clientes que leem campo `mensagem` quebram | Período de transição: manter `mensagem` como alias deprecated no schema intermediário; remover em v2.0.0 |
| Categorias normalizadas (UPPER → snake_case) | Clientes que filtram por nome exato de categoria precisam atualizar | Publicar enum oficial de categorias na v1.3.0; deprecar nomes antigos |
| Arquivo `programação ia.json` → `ia_config.json` | Scripts/imports que referenciam o nome antigo | Manter arquivo antigo como symlink/alias; documentar rename |

### 7.2 Plano de Migração por Versão

```
v1.2.0 (atual)    ──▶  v1.3.0 (esta PR)     ──▶  v2.0.0 (futura)
                        │                          │
                        │ • Schema normalizado      │ • Remove campo 'mensagem'
                        │ • Metadados adicionados   │ • Remove categorias UPPER
                        │ • Duplicatas removidas    │ • Remove ia_config alias
                        │ • Campo 'mensagem'        │ • Pipeline completo
                        │   mantido como alias      │   automatizado
                        │ • ia_config.json criado   │
                        │   (programação ia.json    │
                        │    mantido por compat.)   │
```

---

## 8. Resumo: Antes x Depois

| Aspecto | Antes (v1.2.0) | Depois (v1.3.0+) |
|---|---|---|
| **Schema** | Duplo, inconsistente (mensagem/pergunta) | Único, canônico, validado por JSON Schema |
| **Metadados** | Ausentes | id, hash, versao, criado_em, atualizado_em, origem, ativo |
| **Categorias** | Mistas (snake_case + UPPER_CASE) | Enum normalizado (snake_case) |
| **Duplicatas** | 2 diretas confirmadas | Nenhuma (detecção por hash) |
| **Distribuição** | JSON bruto consumido pelo cliente | Artefatos versionados + manifesto + delta |
| **Acoplamento** | Alto (cliente carrega tudo) | Baixo (backend serve sob demanda) |
| **Busca** | Varrimento linear | API com busca semântica (evolução futura) |
| **Versionamento** | Apenas repositório-level | Por repositório E por entrada |
| **Pipeline** | Manual via PR | Automatizado: ingestão→limpeza→validação→publicação |
| **Rastreabilidade** | Ausente | Completa (origem, hash, histórico de versões) |
| **Nome do arquivo** | `programação ia.json` (espaço+acento) | `ia_config.json` (compatível com automação) |

---

## 9. Decisões Técnicas e Trade-offs

| Decisão | Justificativa | Trade-off |
|---|---|---|
| **Hash SHA-256 baseado em conteúdo normalizado** | Determinístico, sem dependência de relógio; permite recomputação | Mudança em qualquer campo muda o hash (intencional) |
| **UUID v5 para IDs** | Determinístico baseado em namespace+conteúdo; evita IDs sequenciais que vazam contagem | Requer definir namespace fixo |
| **snake_case para categorias** | Consistente com convenção Python/SQL/JSON; mais fácil de sanitizar | Requer migração dos consumers que usam UPPER_CASE |
| **Soft delete (`ativo: false`)** | Preserva histórico; evita referências quebradas no backend | Consome mais espaço; consumidores devem filtrar `ativo: true` |
| **Delta incremental por versão** | Reduz payload para clientes; suporta sync eficiente | Requer lógica de aplicação de delta no backend |
| **Sem embedding nesta fase** | Evita overengineering prematuro; embeddings requerem decisão de modelo e infraestrutura | Busca semântica fica para Fase 2-3 |
| **Manter `mensagem` como alias em v1.3.0** | Compatibilidade retroativa; zero breaking change para consumers existentes | Campo legado precisa ser removido em v2.0.0 |

---

## 10. Riscos e Mitigação

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Extensão quebra ao trocar schema | Média | Alto | Manter alias `mensagem` em v1.3.0; remover apenas em v2.0.0 com coordenação |
| Backend não implementa sync incremental | Média | Médio | Snapshot completo (`kb-latest.json`) como fallback sempre disponível |
| Categorias novas não cobertas pelo enum | Média | Baixo | Categoria `outros` como escape hatch; PR de ampliação do enum |
| Hash collision | Muito baixa | Médio | SHA-256: probabilidade negligenciável; detectável se ocorrer |
| Perda de rastreabilidade em migrações manuais | Média | Alto | CI valida presença de todos os campos obrigatórios antes de merge |
| Crescimento descontrolado da base sem revisão de qualidade | Alta | Médio | Gate de revisão humana obrigatório para toda nova entrada |

---

## 11. Pendências com Prioridade

| # | Pendência | Prioridade | Responsável |
|---|---|---|---|
| P1 | Implementar `scripts/pipeline.js`: ingestão → limpeza → validação → publicação | 🔴 Alta | knowledge-base |
| P2 | Criar `schemas/kb-entry.schema.json` (JSON Schema formal) | 🔴 Alta | knowledge-base |
| P3 | Implementar `KB Sync Service` no backend (consome manifesto, aplica delta) | 🔴 Alta | Backend |
| P4 | Implementar `GET /v1/knowledge/search` no backend | 🔴 Alta | Backend |
| P5 | Atualizar Extensão para usar API em vez de JSON local | 🔴 Alta | Extensão |
| P6 | Criar interface de gestão de KB no Admin | 🟡 Média | Admin |
| P7 | Implementar embeddings + busca semântica (pgvector/Pinecone) | 🟡 Média | Backend |
| P8 | Implementar cache com TTL na Extensão | 🟡 Média | Extensão |
| P9 | Adicionar métricas de uso por entrada (quais entradas são mais consultadas) | 🟢 Baixa | Backend |
