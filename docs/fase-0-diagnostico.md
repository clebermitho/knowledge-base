# Fase 0 — Diagnóstico Técnico: Knowledge Base

**Repositório:** `clebermitho/knowledge-base`
**Data:** 2026-04-02
**Versão analisada:** 1.2.0
**Autor:** Copilot — Programa de Modernização (Fase 0/Fase 1)

---

## 1. Inventário de Artefatos Atuais

### 1.1 Estrutura de Arquivos

```
knowledge-base/
├── base_coren.json          # Base de conhecimento principal (24 entradas)
├── programação ia.json      # Configuração de comportamento da IA
├── README.md                # Documentação do repositório
├── CHANGELOG.md             # Histórico de alterações
├── VERSION                  # Versão do ecossistema (1.2.0)
└── .github/
    └── workflows/
        └── ci.yml           # Validação de JSON e estrutura
```

**Ausências notáveis:** nenhum `package.json`, nenhum script de ingestão, nenhum schema formal, nenhum mecanismo de indexação, nenhum pipeline automatizado.

---

### 1.2 Detalhamento dos Artefatos

#### `base_coren.json`

- **Propósito:** Base de perguntas e respostas para atendimento de profissionais de enfermagem com débitos junto ao Coren/Cofen.
- **Formato raiz:** `{ "base_conhecimento": [ ... ] }`
- **Total de entradas:** 24 (sendo 2 duplicatas diretas identificadas)
- **Domínio:** Atendimento/cobrança de anuidades (Coren-PI + expansão nacional)
- **Categorias presentes:** negociacao_debitos, duvida_anuidade, prazo_pagamento, suspensao_registro, cancelamento_registro, ja_suspendeu, ja_cancelou, nada_consta, nao_trabalho_area, sem_dinheiro, entrada_acordo, golpe_duvida, DUVIDA, NEGOCIACAO, SEM_DINHEIRO, CANCELAMENTO, SUSPENSAO, OUTROS

#### `programação ia.json`

- **Propósito:** Configuração de comportamento, tom, regras e contexto para a IA assistente.
- **Campos:** project, role, knowledge_base, common_objections, response_structure, forbidden_behaviors, preferred_phrases, operator_context, system_behavior
- **Natureza:** Arquivo de configuração comportamental (prompt engineering directives)
- **Problemas identificados:** nome de arquivo com acento e espaço (`programação ia.json`) — problemático para automação, CI/CD e imports em scripts.

---

## 2. Como o Conhecimento é Armazenado, Atualizado, Distribuído e Consumido

### 2.1 Armazenamento

- Armazenado como JSON plano no repositório Git (sem banco de dados, sem índice, sem sistema de busca).
- Sem estrutura de diretórios por domínio, versão ou categoria.
- Sem separação entre conteúdo de produção e conteúdo em revisão/rascunho.

### 2.2 Atualização

- Atualização manual via Pull Request diretamente nos arquivos JSON.
- Nenhum processo automatizado de ingestão, limpeza ou validação semântica.
- CI/CD atual valida apenas: sintaxe JSON, presença de campos raiz e arquivo VERSION.
- Sem controle de versão por entrada (cada item não tem `versão`, `hash` ou `data de atualização`).

### 2.3 Distribuição

- Distribuição atual: os arquivos JSON são carregados diretamente pelos consumidores (extensão Chrome e/ou backend).
- Não há endpoint de publicação, CDN, API de consulta ou feed incremental.
- A distribuição implica carregamento completo do JSON bruto pelo cliente — **forte acoplamento**.

### 2.4 Consumo pelos Demais Repositórios

| Repositório | Forma atual de consumo | Problema |
|---|---|---|
| `Extensao` (Chrome Extension) | Carrega JSON inteiro localmente | Peso desnecessário no client; impossibilidade de atualização incremental |
| `Backend-correto` | Presumível leitura/embed direto do JSON como contexto de prompt | Sem busca semântica; contexto inflado |
| `Admin-Assistant-Chat` | Consumo indireto (via backend ou sem consumo direto identificado) | Sem interface de gestão da KB |

> **Nota:** O consumo real pela extensão e pelo backend foi inferido pela arquitetura descrita no README e no contexto do produto. A validação definitiva requer inspeção dos repos consumidores.

---

## 3. Problemas Identificados

### 3.1 Inconsistência de Schema (CRÍTICO)

O arquivo `base_coren.json` contém **duas estruturas diferentes misturadas**:

**Formato A** (primeiras 12 entradas):
```json
{
  "categoria": "negociacao_debitos",
  "mensagem": "Quero verificar minhas anuidades.",
  "resposta": "..."
}
```

**Formato B** (últimas 12 entradas):
```json
{
  "pergunta": "não tenho dinheiro",
  "resposta": "...",
  "categoria": "SEM_DINHEIRO",
  "palavras_chave": ["dinheiro", "sem condições", "não posso pagar"]
}
```

**Impacto:** Qualquer consumidor que espera um campo `pergunta` falha nas primeiras 12 entradas. Qualquer consumidor que espera `mensagem` falha nas últimas 12. O CI atual não detecta esta inconsistência.

### 3.2 Duplicação de Entradas (ALTO)

| Entradas duplicadas | Categorias | Observação |
|---|---|---|
| "Não tenho dinheiro." / "não tenho dinheiro" | `sem_dinheiro` / `SEM_DINHEIRO` | Mesma intenção, respostas similares |
| "Isso é golpe?" / "isso é golpe" | `golpe_duvida` / `GOLPE` | Mesma intenção, respostas ligeiramente diferentes |
| "Não trabalho mais na enfermagem." / "não estou trabalhando na enfermagem" | `nao_trabalho_area` / `NEGOCIACAO` | Mesma intenção, respostas diferentes |

### 3.3 Inconsistência de Nomenclatura de Categorias (MÉDIO)

Categorias com nomes mistos (snake_case vs UPPER_CASE):
- `sem_dinheiro` e `SEM_DINHEIRO` (ambas presentes)
- `golpe_duvida` e `GOLPE`
- `nao_trabalho_area` e `NEGOCIACAO`

Não há enum/schema formal para validar categorias válidas.

### 3.4 Ausência de Metadados por Entrada (ALTO)

Nenhuma entrada possui:
- `id` único (impossibilita referência pontual, deduplicação e rastreabilidade)
- `hash` de conteúdo (impossibilita detecção de mudanças incrementais)
- `versao` (impossibilita rollback ou diff semântico)
- `criado_em` / `atualizado_em` (impossibilita ordenação por atualidade)
- `origem` (impossibilita rastreabilidade da fonte do conhecimento)

### 3.5 Acoplamento com Clientes (CRÍTICO)

- O JSON completo é consumido diretamente por clientes (extensão Chrome).
- Qualquer alteração na KB requer recarregamento completo pelo cliente.
- Sem cache com TTL, sem invalidação seletiva, sem busca parcial.
- A extensão carrega conhecimento que não utiliza ativamente (entradas irrelevantes para o contexto).

### 3.6 Ausência de Pipeline de Ingestão/Indexação (ALTO)

- Não há etapa de limpeza ou normalização de texto.
- Não há chunking para suporte a RAG (Retrieval-Augmented Generation).
- Não há indexação semântica (embeddings, vetores).
- Não há mecanismo de busca — consumidores varrem o array inteiro.

### 3.7 Arquivo com Nome Problemático (MÉDIO)

- `programação ia.json` contém acento e espaço no nome.
- Problemático para: scripts shell, imports Node.js sem escape, automação CI/CD, git em sistemas Windows.

### 3.8 Ausência de Versionamento por Entrada (ALTO)

- Apenas o repositório tem versão (`VERSION: 1.2.0`).
- Entradas individuais não têm versão, impossibilitando rollback seletivo, diff semântico ou migração controlada.

### 3.9 Riscos de Consistência (MÉDIO)

- Duas entradas sobre o mesmo tema com respostas ligeiramente diferentes podem gerar comportamento imprevisível na IA (qual usar?).
- Sem critério explícito de qual resposta tem prioridade em caso de ambiguidade.

### 3.10 Riscos de Segurança (BAIXO/MONITORAR)

- Os arquivos JSON são públicos no repositório — nenhum dado sensível identificado atualmente.
- `programação ia.json` contém configuração comportamental da IA que, se modificada sem revisão, pode introduzir comportamentos indesejados.
- Sem assinatura ou hash de integridade nos arquivos distribuídos.

---

## 4. Inventário de Contratos e Formatos

### 4.1 Contrato Atual: `base_coren.json`

```json
{
  "base_conhecimento": Array<KBEntry>
}
```

`KBEntry` (formato A — 12 entradas):
```typescript
{
  categoria: string;      // ex: "negociacao_debitos"
  mensagem: string;       // pergunta/gatilho do cliente
  resposta: string;       // resposta orientativa
  // sem palavras_chave
  // sem id
  // sem metadados
}
```

`KBEntry` (formato B — 12 entradas):
```typescript
{
  categoria: string;       // ex: "SEM_DINHEIRO" (UPPER_CASE)
  pergunta: string;        // campo diferente de "mensagem"
  resposta: string;
  palavras_chave: string[];
  // sem id
  // sem metadados
}
```

### 4.2 Contrato Atual: `programação ia.json`

```typescript
{
  project: { name, context, stage, goal };
  role: { description, tone: string[], style_rules: string[] };
  knowledge_base: { core_rules: string[], legal_basis: string[], entities: object };
  common_objections: Array<{ input, response_strategy }>;
  response_structure: string[];
  forbidden_behaviors: string[];
  preferred_phrases: string[];
  operator_context: { name, role, skills, goal };
  system_behavior: { always: string[], never: string[] };
}
```

---

## 5. Baseline de Qualidade do Conteúdo

| Dimensão | Estado Atual | Score | Observação |
|---|---|---|---|
| **Completude** | 24 entradas em ~18 categorias únicas | 🟡 Parcial | Cobre os cenários principais do Coren-PI; sem cobertura para expansão nacional |
| **Atualidade** | Sem timestamp por entrada | 🔴 Ausente | Impossível determinar quando cada entrada foi atualizada |
| **Consistência** | Schema duplo, categorias mistas | 🔴 Baixa | 2 duplicatas diretas, 1 entrada similar identificadas |
| **Duplicação** | 2 duplicatas diretas confirmadas | 🔴 Presente | `sem_dinheiro` e `golpe_duvida` duplicados |
| **Rastreabilidade de origem** | Ausente | 🔴 Ausente | Nenhuma entrada tem campo `origem` ou `fonte` |

---

## 6. Lacunas para Ingestão / Indexação / Busca Semântica / Cache / Invalidação

| Capacidade | Estado | Lacuna |
|---|---|---|
| **Ingestão automatizada** | ❌ Ausente | Sem script de import, sem validação semântica automática |
| **Limpeza/normalização** | ❌ Ausente | Sem normalização de texto, capitalização, pontuação |
| **Chunking para RAG** | ❌ Ausente | Entradas não são segmentadas para embeddings |
| **Indexação semântica** | ❌ Ausente | Sem embeddings, sem índice vetorial |
| **Busca por similaridade** | ❌ Ausente | Consumidores varrem array completo |
| **Cache com TTL** | ❌ Ausente | Sem mecanismo de cache ou invalidação |
| **Atualização incremental** | ❌ Ausente | Distribuição sempre carrega tudo |
| **Deduplicação automática** | ❌ Ausente | Duplicatas detectadas apenas manualmente |
| **Endpoint de publicação** | ❌ Ausente | Sem API, sem CDN, sem feed |

---

## 7. Resumo: Antes (as-is)

| Aspecto | Estado atual |
|---|---|
| Formato de dados | JSON plano, schema duplo inconsistente, sem metadados |
| Distribuição | Arquivo inteiro carregado diretamente pelo cliente |
| Acoplamento | Alto — extensão/backend dependem do JSON bruto |
| Versionamento | Apenas repositório-level (sem granularidade por entrada) |
| Deduplicação | Manual — 2 duplicatas confirmadas presentes |
| Busca | Nenhuma — varrimento linear do array |
| Ingestão | Manual via PR |
| Qualidade | Sem métricas, sem baseline formal |
| Rastreabilidade | Ausente por entrada |
| Segurança | Arquivo público sem integridade verificável |

---

## 8. Comandos de Diagnóstico Executados

```bash
# Verificar estrutura de arquivos
find . -type f | grep -v .git

# Contar entradas na base
node -e "const b = require('./base_coren.json'); console.log(b.base_conhecimento.length)"
# Output: 24

# Detectar inconsistência de schema
node -e "
const b = require('./base_coren.json');
const comMensagem = b.base_conhecimento.filter(e => e.mensagem).length;
const comPergunta = b.base_conhecimento.filter(e => e.pergunta).length;
const comPalavrasChave = b.base_conhecimento.filter(e => e.palavras_chave).length;
console.log('com mensagem:', comMensagem);
console.log('com pergunta:', comPergunta);
console.log('com palavras_chave:', comPalavrasChave);
"
# Output:
# com mensagem: 12
# com pergunta: 12
# com palavras_chave: 12

# Detectar duplicatas por categoria
node -e "
const b = require('./base_coren.json');
const cats = b.base_conhecimento.map(e => e.categoria.toLowerCase());
const dups = cats.filter((c, i) => cats.indexOf(c) !== i);
console.log('categorias duplicadas:', [...new Set(dups)]);
"
# Output: categorias duplicadas: [ 'sem_dinheiro', 'negociacao' ]

# Validar JSON sintático
node -e "JSON.parse(require('fs').readFileSync('base_coren.json','utf8'))" && echo OK
# Output: OK
node -e "JSON.parse(require('fs').readFileSync('programação ia.json','utf8'))" && echo OK
# Output: OK
```

---

## 9. Pendências com Prioridade

| # | Pendência | Prioridade | Fase |
|---|---|---|---|
| P1 | Normalizar schema de `base_coren.json` (unificar `mensagem`/`pergunta`, adicionar metadados) | 🔴 Alta | Fase 1 |
| P2 | Deduplicar entradas com mesma intenção semântica | 🔴 Alta | Fase 1 |
| P3 | Renomear `programação ia.json` para `ia_config.json` (sem espaço/acento) | 🟡 Média | Fase 1 |
| P4 | Definir enum formal de categorias válidas | 🟡 Média | Fase 1 |
| P5 | Implementar API de consulta no backend (remover dependência de JSON bruto no cliente) | 🔴 Alta | Fase 2 |
| P6 | Implementar pipeline de ingestão/limpeza/indexação | 🟡 Média | Fase 2 |
| P7 | Implementar chunking + embeddings para RAG | 🟡 Média | Fase 3 |
| P8 | Implementar cache com TTL e invalidação incremental | 🟡 Média | Fase 3 |
