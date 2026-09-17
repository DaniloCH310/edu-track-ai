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

Os verbos **DEVE**, **NÃO DEVE** e **PODE** indicam requisitos normativos. Exemplos de interface não substituem os cenários de aceite.
