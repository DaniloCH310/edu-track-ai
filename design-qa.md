# Design QA — Jornada de aprendizagem

## Evidências

- Fonte visual: `C:\Users\DaniloChavesdeSá\.codex\generated_images\01a044d8-1389-7560-8df3-1c0b1ec41aa8\exec-10661b20-ef80-4b9f-9a18-29be8d6ac105.png`
- Implementação renderizada: `tmp/ui/dashboard-journey-open.png`
- Comparação combinada: `tmp/ui/design-comparison.png`
- Responsividade: `tmp/ui/dashboard-mobile.png`
- Viewport principal: 1536 × 1024 CSS px, DPR 1
- Fonte: 1536 × 1024 px
- Implementação: 1536 × 1024 px
- Normalização: nenhuma; dimensões e densidade coincidem
- Estado: tema claro, usuário autenticado, uma disciplina concluída, agenda vazia e tooltip da ilha aberto

## Comparação visual

### Tela completa

A comparação combinada mostra a mesma hierarquia do conceito: sidebar fixa, saudação e ação primária, quatro métricas, jornada como área dominante e agenda à direita. As proporções, o ritmo vertical, os raios, a paleta e a densidade permanecem equivalentes. A implementação utiliza somente a disciplina existente; não inventa as duas disciplinas ilustrativas do mockup.

### Recorte da jornada

O recorte ampliado confirma a fidelidade do asset isométrico, a transparência limpa, a nitidez em escala, as posições relativas das ilhas e a legenda. O tooltip é UI real e legível, com progresso, tarefas e prazo derivados da API. Não foi necessário outro recorte: tipografia, labels, bordas, ícones e transparência estão legíveis no comparativo combinado.

## Superfícies obrigatórias

- Fontes e tipografia: a hierarquia, pesos, tamanhos e quebras seguem a referência; Segoe UI Variable mantém boa leitura e aproxima o sans-serif do conceito.
- Espaçamento e layout: grid, margens, paddings, altura dos painéis e distribuição desktop/mobile não apresentam corte ou overflow.
- Cores e tokens: roxo, verde, laranja, lavanda, estados semânticos e contraste mapeiam os tokens existentes do EduTrack.
- Imagens e assets: as ilhas e o calendário são assets raster próprios, nítidos e com transparência real; os ícones de UI vêm da biblioteca Phosphor local.
- Copy e conteúdo: rótulos em português foram preservados. Valores e prazos refletem a API, inclusive quando diferem dos dados fictícios do conceito.

## Histórico de comparação

1. Primeira captura: foi identificado um P2 no tooltip da ilha concluída, que invadia o cabeçalho e era capturado antes do fim da transição.
2. Correções: tooltip reposicionado lateralmente, tratamento móvel separado e espera de 250 ms adicionada à captura automatizada.
3. Pós-correção: `tmp/ui/design-comparison.png` confirma tooltip legível, sem sobreposição crítica, e composição equivalente ao conceito.

## Findings

Nenhuma diferença P0, P1 ou P2 permanece.

- P3: o conceito mostra labels fictícios para três disciplinas, enquanto a implementação exibe somente dados reais. Essa diferença é intencional e evita conteúdo enganoso.
- P3: o pequeno ícone informativo decorativo do conceito foi omitido porque não havia uma ação correspondente definida.

## Interações e qualidade técnica verificadas

- Fluxo disciplina → tarefa → conclusão → dashboard.
- Clique/toque e foco no hotspot da ilha.
- Abertura do tooltip e atualização do atributo `aria-expanded`.
- Dashboard em 1536 × 1024 e 390 × 844.
- Ausência de overflow horizontal no celular.
- Console verificado sem erros depois da autenticação; o 401 inicial da consulta anônima é esperado e foi isolado no teste.

## Implementation Checklist

- [x] Assets finais inseridos no projeto.
- [x] Dados da API conectados à jornada.
- [x] Interação por mouse, teclado e toque.
- [x] Layout desktop e móvel validado.
- [x] Console e fluxo principal validados.

final result: passed
