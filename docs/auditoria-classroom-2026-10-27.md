# EduTrack — comparação com os requisitos da disciplina

Data: 27/10/2026. Base do código: `47db65a`, branch `main`.

## Resultado

O projeto tem o núcleo funcional previsto: autenticação, recuperação de senha, disciplinas, tarefas, progresso e EDU IA. Entretanto, ainda há lacunas para a entrega acadêmica, principalmente relatório PDF e validação do OpenSpec. Existência de código não substitui uma demonstração completa funcionando.

Esta revisão comparou os materiais acessados no Classroom pelo navegador com o repositório. Não alterou funcionalidades, não submeteu atividades e não repetiu testes funcionais no navegador. A ausência de uma evidência no repositório não significa que ela não exista em outra pasta ou em uma entrega anterior.

## Entrega final mais recente

[Entrega final do Projeto](https://classroom.google.com/u/1/c/ODcxMjM5MzQ4NTUz/a/ODk2MjIzMTE0MDc0/details), com prazo exibido de **23 de novembro, às 23h59**.

O professor pede:

- Vídeo apresentando login, recuperação de senha, cadastro de usuário, IA, relatório, disciplinas e tarefas.
- Apresentação do banco de dados e do modelo.
- Apresentação do GitHub, detalhando estrutura, programas e OpenSpec.
- É permitido fazer um vídeo para cada etapa.

As avaliações parciais 01 e 02 aparecem como concluídas no Classroom. Isso não comprova, isoladamente, a entrega das evidências de todas as 16 tarefas.

## Pendências prioritárias

| Prioridade | Achado | Evidência e ação recomendada |
|---|---|---|
| 1 | OpenSpec não passa na validação oficial | `openspec validate --all --strict --no-interactive` resultou em **0 aprovados e 8 falhas**. Sete specs não têm as seções exigidas `## Purpose` e `## Requirements`; a proposta `add-edu-ia` não tem deltas. Corrigir o formato, reconciliar o conteúdo com o código e arquivar mudanças concluídas. |
| 2 | Relatório semanal PDF ausente | Não há API de relatórios nem gerador PDF nas dependências/código examinados. O fechamento semanal da interface não é um PDF. Implementar download autenticado, com disciplinas, tarefas e progresso, respeitando o usuário logado. A tarefa 15 pede `/reports/generate`. |
| 3 | Evidências finais ainda precisam ser conferidas | Preparar os vídeos exigidos e demonstrar o fluxo completo, inclusive relatório. O roteiro atual em `docs/roteiro-avaliacao-parcial-02.md` é da avaliação parcial e precisa de uma versão final. |
| 4 | Fluxo acadêmico de PR não demonstrado | A consulta ao GitHub não retornou PRs. A tarefa 5 pede PR mesclado; a tarefa 16 pede PR `release/final-delivery` aberto, sem mesclar, para o professor. São evidências distintas. Não fabricar histórico retroativo. |
| 5 | Publicação pública não comprovada nesta auditoria | Existem `render.yaml` e `docs/production.md`. Configuração de implantação não comprova um serviço publicado e acessível. Verificar URL real e adequação à trilha aceita pelo professor. |

Ordem sugerida: regularizar o OpenSpec, especificar e implementar o PDF, validar o fluxo completo, organizar publicação/PR/evidências e gravar a apresentação.

## Matriz das 16 tarefas

Conforme informado pelo aluno após a revisão, o professor autorizou ferramentas alternativas. “Equivalente” indica que o objetivo da atividade deve ser demonstrado na arquitetura atual; não é necessário reproduzir ferramentas específicas como FlutterFlow ou Xano. Essa autorização não dispensa os requisitos funcionais e as evidências de entrega.

| Tarefa | Exigência principal | Situação encontrada |
|---|---|---|
| 01 | Git, GitHub, README e primeiro ciclo de commit/push | Repositório e histórico presentes; conferir prints individuais exigidos. |
| 02 | Ambiente VS Code, Node/npm, Gemini Code Assist e XanoScript | Apresentar o ambiente equivalente usado no projeto; a ausência de XanoScript não é pendência com a substituição de ferramentas autorizada. |
| 03 | Inicialização OpenSpec e estrutura de especificações | Estrutura parcial; validação falha e `openspec/AGENTS.md` não encontrado. |
| 04 | Pull/push de XanoScript e arquivos `.xs` | Demonstrar o equivalente com modelos, migrações e versionamento em FastAPI/PostgreSQL. Não é necessário adicionar Xano ou arquivos `.xs` apenas para reproduzir a ferramenta do roteiro. |
| 05 | Branch, PR e merge | Há commits, mas nenhum PR retornado pela consulta ao GitHub. |
| 06 | Pesquisa de pelo menos dois templates Figma | `docs/pesquisa/referencias.md` não encontrado; faltam links, justificativas e evidência do PR no repositório. |
| 07 | Configurar frontend e conexão ao backend | Equivalente funcional na arquitetura própria, com uso de ferramentas alternativas autorizado. |
| 08 | Proposta OpenSpec de disciplinas, validação e arquivamento | CRUD existe; histórico arquivado solicitado não foi encontrado. |
| 09 | Páginas, navegação e referências visuais | Interface existente; conferir evidências Figma e PR exigidas. |
| 10 | AGENTS.md com perfil do projeto e convenções | Arquivo da raiz contém somente orientações Graphify. Complementar arquitetura, convenções, isolamento por usuário e fluxo OpenSpec. |
| 11 | Modelo de tarefas vinculado a disciplinas e OpenSpec | Modelo presente em `app/models/task.py`; falta demonstrar o ciclo OpenSpec exigido. A substituição do Xano está contemplada pela autorização de ferramentas alternativas. |
| 12 | Script Python de progresso com JSON `percentage` | Cálculo equivalente em `app/services/dashboard.py`, incluindo total zero. `scripts/calculate_progress.py`, artefato solicitado, não encontrado. |
| 13 | CRUD autenticado de disciplinas e isolamento por usuário | Rotas e filtros de propriedade presentes. Atualização usa PUT, enquanto o exercício exemplifica PATCH. Demonstrar API e isolamento. |
| 14 | Busca avançada de disciplinas/tarefas na trilha original | Tarefas têm filtros; listagem de disciplinas não tem parâmetro de busca. O resumo Streamlit apresenta uma atividade diferente, de gráfico; confirmar qual trilha vale. |
| 15 | Geração e download de PDF com progresso | Pendente no código examinado. |
| 16 | Auditoria, specs arquivadas, fluxo completo, PR final e reflexão | Parcial: README e CI existem; faltam OpenSpec válido, PDF e evidências de PR final, publicação e reflexão. |

## O que já serve de base para a apresentação

- APIs em `app/api/auth.py`, `app/api/subjects.py`, `app/api/tasks.py`, `app/api/dashboard.py` e `app/api/edu_ia.py`.
- Entidades em `app/models/` e documentação em `docs/dicionario-de-dados/README.md`, com dez imagens de tabelas em `docs/dicionario-de-dados/prints/`.
- Progresso calculado em Python em `app/services/dashboard.py`.
- Fechamento semanal em `app/static/js/weekly-review.js`, útil como base para definir os dados do PDF.
- Especificações em `openspec/specs/`, que precisam ser adequadas ao formato validado pela CLI.
- [CI do commit auditado](https://github.com/DaniloCH310/edu-track-ai/actions/runs/40597867736) concluída com sucesso. Essa CI não valida o OpenSpec. A execução anterior de testes registrou 119 testes aprovados; não foi repetida nesta auditoria.

Para apresentar o banco e o modelo, mostrar relações e chaves, além do dicionário. Conferir a correspondência com as migrações e com o banco efetivamente usado na demonstração.

## Ferramentas autorizadas e diferenças de escopo

Os materiais contêm uma trilha FlutterFlow + Xano e outra Streamlit + Xano. O EduTrack usa HTML/CSS/JavaScript + FastAPI + PostgreSQL. **O aluno confirmou que o professor autorizou outras ferramentas**, portanto essa escolha não é uma pendência e não requer nova confirmação. A apresentação deve explicar como a arquitetura atual atende aos objetivos das atividades. Não é necessário migrar para FlutterFlow, Streamlit ou Xano.

As especificações também citam tempo estimado versus real, progresso ponderado e previsão de conclusão. A tarefa atual tem `estimated_minutes`, mas não um registro de tempo real. Esses itens aparecem como evolução futura em partes do documento e como recursos avançados em outras: devem ser esclarecidos antes de tratá-los como bloqueadores da entrega. Push notifications são descritas como integração futura.

`openspec/project.md` ainda classifica estimativas de tempo como futuras, embora já existam no modelo: atualizar essa documentação. Não foram verificados nesta revisão carga de 1.000 usuários, latência inferior a dois segundos ou conformidade completa de acessibilidade.

## Fontes consultadas

- [Classroom — atividades da disciplina](https://classroom.google.com/u/1/w/ODcxMjM5MzQ4NTUz/t/all).
- [Publicação dos planos e especificações](https://classroom.google.com/u/1/c/ODcxMjM5MzQ4NTUz/m/ODY5MDkyMDk2MDYy/details).
- [Publicação com as 16 tarefas](https://classroom.google.com/u/1/c/ODcxMjM5MzQ4NTUz/m/ODY5MDkyMDU0MDg4/details).
- [Plano original](https://drive.google.com/file/d/1W09chBXs6nurJ7myyQ-pt5WwEGprqrOE/view).
- [Especificação de negócio](https://docs.google.com/document/d/1SbPo_heMZiWBjsU3O01pDukxWiVjYSc_bXjpr9YpmFM/edit).
- [Especificação complementar](https://docs.google.com/document/d/1a4bTOpVvNdd4iNnVWKF1gwKHZrfiBgkbac9l0JndoyQ/edit).
- [Plano Streamlit](https://drive.google.com/file/d/1hePTH6I4izZ8SePV2P9lJ70wh6yLngJa/view).
- [Especificação Streamlit](https://drive.google.com/file/d/1-VTn5SeeH0b1YCBCVg75U2PCM6My9hfP/view).
- [Resumo das tarefas Streamlit](https://drive.google.com/file/d/13wCiw7FQndwbEqj7jBvQa65VgGa6ASel/view).
- [Tarefa 15 — PDF](https://drive.google.com/file/d/1itVS4b3t8sDvBWbPgkVc_ATaRH506IMM/view).
- [Tarefa 16 — entrega](https://drive.google.com/file/d/1Pdkt2OV-6KWKuNyrtD2yIg5oALsKunyQ/view).

Este documento registra a situação encontrada, não a conclusão das correções recomendadas.
