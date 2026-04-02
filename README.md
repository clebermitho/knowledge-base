# 📚 Chatplay Knowledge Base

Base de conhecimento centralizada para o assistente IA do **Chatplay Assistant** — plataforma de atendimento inteligente para profissionais de enfermagem (Coren/Cofen).

> **v1.3.0**: Schema normalizado com metadados por entrada, deduplicação, categorias padronizadas e documentação de arquitetura alvo. Ver [docs/fase-0-diagnostico.md](docs/fase-0-diagnostico.md) e [docs/fase-1-arquitetura-alvo.md](docs/fase-1-arquitetura-alvo.md).

## 📁 Estrutura de Arquivos

```
knowledge-base/
├── base_coren.json          # Base de conhecimento (22 entradas, schema v1.3.0)
├── ia_config.json           # Configuração de comportamento da IA (nome canônico)
├── programação ia.json      # Mantido por compatibilidade (deprecated — use ia_config.json)
├── schemas/
│   └── kb-entry.schema.json # JSON Schema formal para validação de entradas
├── docs/
│   ├── fase-0-diagnostico.md     # Diagnóstico técnico completo (as-is)
│   └── fase-1-arquitetura-alvo.md # Arquitetura alvo (to-be)
├── README.md
├── CHANGELOG.md
└── VERSION
```

## 📐 Schema de Entrada (`base_coren.json`)

Cada entrada segue o schema canônico v1.3.0:

```json
{
  "id": "kb_coren_001",
  "categoria": "negociacao_debitos",
  "pergunta": "Quero verificar minhas anuidades.",
  "resposta": "Olá profissional...",
  "palavras_chave": ["anuidade", "verificar", "débito"],
  "metadata": {
    "versao": "1.0.0",
    "hash": "sha256:6d3965e2653f228396a8a0c70581ef9dcdb367f83774acef72bd35bb1ce994c4",
    "origem": "manual_coren_pi_v1",
    "criado_em": "2026-03-29T00:00:00Z",
    "atualizado_em": "2026-04-02T00:00:00Z",
    "ativo": true
  }
}
```

**Campos obrigatórios por entrada:** `id`, `categoria`, `pergunta`, `resposta`, `palavras_chave`, `metadata` (com `versao`, `hash`, `origem`, `criado_em`, `atualizado_em`, `ativo`).

## 🏷️ Categorias da Base Coren

| Categoria | Descrição |
|-----------|-----------|
| `negociacao_debitos` | Verificação e negociação de anuidades |
| `duvida_anuidade` | Explicação sobre obrigatoriedade da anuidade |
| `prazo_pagamento` | Solicitações de prazo / intenção de adiar |
| `suspensao_registro` | Orientação sobre suspensão de inscrição |
| `cancelamento_registro` | Orientação sobre cancelamento de inscrição |
| `ja_suspendeu` / `ja_cancelou` | Acompanhamento pós-solicitação |
| `nada_consta` | Emissão de certidão Nada Consta |
| `nao_trabalho_area` | Profissionais que não atuam mais na enfermagem |
| `sem_dinheiro` | Situações de dificuldade financeira / desemprego |
| `entrada_acordo` | Dúvidas sobre entrada em acordos |
| `golpe_duvida` | Validação de legitimidade do contato |
| `consequencias_debito` | Dúvidas sobre consequências do não pagamento |
| `endereco_coren` | Endereços das sedes do Coren |
| `outros` | Outros assuntos não categorizados |

## 🤖 Configuração da IA (`ia_config.json`)

O arquivo define:
- **Projeto**: Assistente Operacional Coren/Cofen (Pagueplay)
- **Tom**: Humano, empático, consultivo, institucional
- **Regras de estilo**: 7 regras de conduta
- **Base legal**: Lei 5.905/1973, Lei 12.514/2011, Lei 7.498/1986
- **Objeções comuns**: 6 cenários com estratégias de resposta
- **Estrutura de resposta**: 5 etapas (validar → explicar → consequência → solução → abertura)
- **Comportamentos proibidos**: 6 restrições
- **Frases preferidas**: 6 expressões padrão

> **Nota:** `programação ia.json` é mantido por compatibilidade retroativa. Use `ia_config.json` em novos scripts e automações.

## 🔧 Como Contribuir

### Adicionar nova entrada

1. Edite `base_coren.json` seguindo o schema canônico v1.3.0:
   ```json
   {
     "id": "kb_coren_023",
     "categoria": "outros",
     "pergunta": "Sua pergunta aqui.",
     "resposta": "Resposta completa aqui.",
     "palavras_chave": ["palavra1", "palavra2"],
     "metadata": {
       "versao": "1.0.0",
       "hash": "sha256:COMPUTE_BEFORE_COMMIT",
       "origem": "manual_coren_pi_v1",
       "criado_em": "YYYY-MM-DDTHH:MM:SSZ",
       "atualizado_em": "YYYY-MM-DDTHH:MM:SSZ",
       "ativo": true
     }
   }
   ```
2. Valide o JSON: `node -e "JSON.parse(require('fs').readFileSync('base_coren.json','utf8')); console.log('OK')"`
3. Verifique duplicatas por categoria antes de commitar.
4. Abra um Pull Request para revisão.

### Desativar entrada (sem remover)

Altere `metadata.ativo` para `false` em vez de remover a entrada — isso preserva o histórico e evita referências quebradas no backend.

## 🏗️ Arquitetura e Boundary

Este repositório é a **fonte de verdade** da base de conhecimento. Ele:
- ✅ Produz artefatos versionados para o backend consumir
- ✅ Mantém histórico completo de entradas (incluindo desativadas)
- ❌ **Não** serve HTTP diretamente
- ❌ **Não** é consumido diretamente pela extensão Chrome (usar API do backend)

Ver [docs/fase-1-arquitetura-alvo.md](docs/fase-1-arquitetura-alvo.md) para o fluxo completo.

## 🔗 Repositórios Relacionados

| Repositório | Função |
|-------------|--------|
| [Backend-correto](https://github.com/clebermitho/Backend-correto) | Consome esta KB, expõe `/v1/knowledge` para os clientes |
| [Admin-Assistant-Chat](https://github.com/clebermitho/Admin-Assistant-Chat) | Painel administrativo — gestão e monitoramento da KB |
| [Extensao](https://github.com/clebermitho/Extensao) | Extensão Chrome — consome KB via API do backend (thin client) |

## 📋 Versionamento

- **Versão do ecossistema**: Consulte o arquivo `VERSION`
- Todos os repositórios seguem [Semantic Versioning](https://semver.org/)
- Cada entrada possui versão individual no campo `metadata.versao`
