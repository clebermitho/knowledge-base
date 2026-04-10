# 📚 Chatplay Knowledge Base

Repositório canônico da base de conhecimento do ecossistema Chatplay.

## ✅ Contrato canônico (breaking change)

A fonte oficial passou a ser **um único arquivo**:

- `base-conhecimento.json`

Modelos legados de duas bases (`base_coren.json` + `programação ia.json`) e placeholders antigos (`{{BASE_COREN}}`, `{{BASE_SISTEMA}}`) **não são mais o contrato principal**.

## 📁 Estrutura atual

| Arquivo | Papel |
|---------|-------|
| `base-conhecimento.json` | Base unificada canônica consumida pelos demais repositórios |
| `VERSION` | Versão do ecossistema |
| `CHANGELOG.md` | Histórico de mudanças e breaking changes |

## 🧩 Estrutura mínima de `base-conhecimento.json`

Chaves obrigatórias validadas em CI:

- `project`
- `behavior`
- `core_rules`
- `intelligence`
- `procedures`
- `response_patterns`
- `objections`
- `contacts`
- `security_rules`
- `fallback`
- `response_model`

## 🔄 Migração de consumidores

Repositórios que devem consumir o contrato unificado:

- [Backend-correto](https://github.com/clebermitho/Backend-correto)
- [Admin-Assistant-Chat](https://github.com/clebermitho/Admin-Assistant-Chat)
- [Extensao](https://github.com/clebermitho/Extensao)

## 🔧 Contribuição

1. Edite apenas `base-conhecimento.json` para alterações de conhecimento.
2. Valide o JSON localmente:
   - `node -e "JSON.parse(require('fs').readFileSync('base-conhecimento.json','utf8'))"`
3. Abra PR com impacto e compatibilidade descritos.

## 📋 Versionamento

- Consulte `VERSION`.
- Este repositório segue [Semantic Versioning](https://semver.org/).
