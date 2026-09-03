# Design QA — Campus de aprendizagem

## Evidências

- Verdade visual: `C:\Users\DaniloChavesdeSá\.codex\generated_images\01a044d8-1389-7560-8df3-1c0b1ec41aa8\exec-0a8145b4-f9a4-4a95-a135-cc1604111f91.png`
- Implementação desktop: `C:\Users\DaniloChavesdeSá\Desktop\edu-track-ai-evandro-main\tmp\ui\dashboard-campus-reference-state.png`
- Comparação conjunta: `C:\Users\DaniloChavesdeSá\Desktop\edu-track-ai-evandro-main\tmp\ui\campus-comparison.png`
- Estado interativo focado: `C:\Users\DaniloChavesdeSá\Desktop\edu-track-ai-evandro-main\tmp\ui\dashboard-campus-open.png`
- Implementação móvel: `C:\Users\DaniloChavesdeSá\Desktop\edu-track-ai-evandro-main\tmp\ui\dashboard-mobile.png`
- Viewport desktop: 1440 × 1024 CSS px, deviceScaleFactor 1.
- Pixels da fonte e da implementação: 1440 × 1024 cada; nenhuma normalização de densidade foi necessária.
- Viewport móvel: 390 × 844 CSS px, deviceScaleFactor 1; captura de página completa com 390 px de largura.
- Estado: fonte com quatro disciplinas em progresso misto; implementação com uma disciplina concluída. A diferença é deliberadamente orientada pelos dados reais do teste e não foi usada para julgar quantidade de rótulos.

## Comparação e achados

- Tipografia: família, pesos e hierarquia permanecem coerentes com a interface existente e próximos da referência. Títulos, números e pequenos rótulos continuam legíveis sobre a imagem.
- Espaçamento e composição: o campus ocupa a região principal, mantém a praça central como foco e posiciona missão, progresso e disciplinas como camadas funcionais. A faixa de métricas existente foi preservada no lugar do “ritmo da semana” da referência para não remover indicadores do produto.
- Cores e tokens: violeta, verde de conclusão, laranja de próxima etapa e superfícies claras usam os tokens existentes. Contraste e tratamento de tema escuro foram mantidos.
- Imagem: o ativo é uma ilustração 3D real gerada para o espaço, sem textos ou dados embutidos. O recorte 16:9, a nitidez e a distribuição dos quatro prédios correspondem à direção selecionada.
- Conteúdo: nomes, percentuais, marcos, prazos, missão recomendada e progresso geral são HTML dinâmico alimentado pela API. Não há conteúdo acadêmico fixo na imagem.
- Interação focada: o prédio abre um painel com progresso, quantidade de tarefas e próximo prazo. Foco, clique, estados concluído/em andamento/próximo/bloqueado e redução de movimento foram verificados.
- Responsividade: no celular, a imagem vira uma abertura panorâmica e cada disciplina passa a ser um cartão legível; não há overflow horizontal.
- Console: o teste E2E monitorou `console.error` e `pageerror`; nenhum erro foi encontrado.

## Histórico da comparação

1. Primeiro passe: o plano recomendado e o cabeçalho do campus ocupavam fluxo vertical, deixando parte relevante do mapa abaixo da dobra; o cabeçalho também interceptava o clique do prédio à esquerda.
2. Correções: o plano foi convertido em missão sobreposta, o cabeçalho virou um selo compacto sem captura de ponteiro e o painel vazio de entregas deixou de ocupar espaço.
3. Evidência pós-correção: a comparação conjunta mostra o campus completo dentro do mesmo viewport da referência; o teste focado confirma o tooltip operacional e a captura móvel confirma a adaptação sem overflow.

## Pendências de baixa prioridade

- P3: em uma evolução futura, a faixa de métricas pode ganhar o ritmo diário da semana sem substituir os quatro indicadores atuais.
- P3: uma conta com quatro disciplinas fornece uma demonstração visual mais próxima do mock do que o estado automatizado com uma única disciplina.

## Checklist de implementação

- [x] Campus responsivo com ativo dedicado.
- [x] Até quatro prédios associados por tipo de disciplina.
- [x] Progresso, marcos e estados dinâmicos.
- [x] Missão recomendada integrada ao mapa.
- [x] Estado vazio e próximas entregas preservados.
- [x] Clique, foco, tema escuro e movimento reduzido.
- [x] Testes de API, E2E, lint do aplicativo e sintaxe JavaScript.

final result: passed
