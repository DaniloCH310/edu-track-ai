# OpenSpec do EduTrack

Esta pasta é a fonte canônica das regras atuais do produto. Ela complementa os documentos históricos em `docs/superpowers/specs/`, que preservam o raciocínio e as decisões de cada entrega.

## Estrutura

- `project.md`: contexto do produto, arquitetura, limites e convenções.
- `specs/<capacidade>/spec.md`: comportamento já aceito para cada capacidade.
- `changes/<identificador>/`: propostas futuras, antes de alterar o código.

## Fluxo para uma próxima mudança

1. Crie `openspec/changes/<identificador>/proposal.md` com problema, objetivo, escopo e não escopo.
2. Crie `tasks.md` com passos verificáveis, arquivos afetados e testes.
3. Acrescente, em `specs/<capacidade>/`, somente os requisitos ou cenários que mudam.
4. Implemente, teste e revise a mudança.
5. Ao concluir, incorpore a regra aceita ao spec canônico e mova a proposta para `changes/archive/`.

Os termos **SHALL** (deve) e **SHALL NOT** (não deve) indicam requisitos normativos. Os títulos `## Purpose`, `## Requirements`, `### Requirement:` e `#### Scenario:` seguem a sintaxe exigida pelo validador; o conteúdo permanece em português. Exemplos de interface não substituem os cenários de aceite.

## Validação

Execute na raiz do projeto, com Node.js 22 disponível:

```powershell
npx --yes @fission-ai/openspec@1.12.0 validate --all --strict --no-interactive
```

O CI executa o mesmo comando em pushes para `main` e em pull requests. A versão é fixada para manter a validação reproduzível.

Mudanças em andamento usam deltas com `## ADDED Requirements`, `## MODIFIED Requirements` ou `## REMOVED Requirements`. Ao concluir, use `openspec archive <identificador>`. Use `--skip-specs` somente quando os requisitos já estiverem incorporados à especificação canônica, para evitar aplicá-los duas vezes. O arquivo histórico preserva a proposta e as tarefas; `validate --all` verifica as especificações atuais e as mudanças ativas.
