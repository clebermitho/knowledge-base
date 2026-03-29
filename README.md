# 📚 Chatplay Knowledge Base

Base de conhecimento centralizada para o assistente IA do **Chatplay Assistant** — plataforma de atendimento inteligente para profissionais de enfermagem (Coren/Cofen).

## 📁 Estrutura de Arquivos

| Arquivo | Descrição | Entradas |
|---------|-----------|----------|
| `base_coren.json` | Respostas para atendimento de profissionais de enfermagem com débitos de anuidade | 24 entradas em 12+ categorias |
| `programação ia.json` | Configuração do comportamento da IA: tom, regras, objeções comuns, estrutura de resposta | Configuração completa do assistente |

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

## 🤖 Configuração da IA (`programação ia.json`)

O arquivo define:
- **Projeto**: Assistente Operacional Coren/Cofen (Pagueplay)
- **Tom**: Humano, empático, consultivo, institucional
- **Regras de estilo**: 7 regras de conduta
- **Base legal**: Lei 5.905/1973, Lei 12.514/2011, Lei 7.498/1986
- **Objeções comuns**: 6 cenários com estratégias de resposta
- **Estrutura de resposta**: 5 etapas (validar → explicar → consequência → solução → abertura)
- **Comportamentos proibidos**: 6 restrições
- **Frases preferidas**: 6 expressões padrão

## 🔧 Como Contribuir

1. Crie um novo arquivo `.json` seguindo a estrutura existente
2. Para a base de atendimento, use o formato:
   ```json
   {
     "categoria": "NOME_DA_CATEGORIA",
     "pergunta": "texto da pergunta",
     "resposta": "texto da resposta",
     "palavras_chave": ["palavra1", "palavra2"]
   }
   ```
3. Valide o JSON antes de commitar: `node -e "JSON.parse(require('fs').readFileSync('arquivo.json','utf8'))"`
4. Abra um Pull Request para revisão

## 🔗 Repositórios Relacionados

| Repositório | Função |
|-------------|--------|
| [Backend-correto](https://github.com/clebermitho/Backend-correto) | API central (Express + Prisma) — auth, eventos, métricas, proxy OpenAI |
| [Admin-Assistant-Chat](https://github.com/clebermitho/Admin-Assistant-Chat) | Painel administrativo (React + TypeScript + Vite) |
| [Arquivos-para-IA](https://github.com/clebermitho/Arquivos-para-IA) | Extensão Chrome (Manifest V3) |

## 📋 Versionamento

- **Versão do ecossistema**: Consulte o arquivo `VERSION`
- Todos os repositórios seguem [Semantic Versioning](https://semver.org/)
