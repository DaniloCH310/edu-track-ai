# Capacidade: organização acadêmica

## Propósito

Permitir que o estudante organize disciplinas e tarefas próprias, enquanto preserva a origem de itens importados do Google Classroom.

## Requisitos

### Requirement: Gestão de disciplinas

O sistema DEVE permitir criar, visualizar, editar e excluir disciplinas do próprio usuário. A disciplina pode conter nome, descrição, professor, período, carga horária e cor visual.

#### Scenario: Criação de uma disciplina

- **WHEN** o usuário registra uma disciplina válida
- **THEN** ela aparece na área Disciplinas e fica disponível para vincular tarefas

#### Scenario: Visualização em distrito acadêmico

- **WHEN** o usuário abre Disciplinas com registros existentes
- **THEN** cada disciplina aparece como um prédio/distrito com progresso, quantidade concluída e dados acadêmicos disponíveis

### Requirement: Gestão de tarefas

O sistema DEVE permitir criar, visualizar, editar, excluir e alterar o status de tarefas associadas a uma disciplina do usuário. Cada tarefa DEVE ter título, prazo e status; descrição é opcional.

#### Scenario: Alteração do status

- **WHEN** o usuário muda uma tarefa para `completed`
- **THEN** o progresso da disciplina e os indicadores dependentes são recalculados

#### Scenario: Lista de missões

- **WHEN** o usuário abre Tarefas
- **THEN** o sistema mostra tarefas como missões, com prazo, disciplina, estado e controles de edição/exclusão

### Requirement: Itens importados preservam sua origem

Disciplinas e tarefas importadas DEVEM ser identificadas como originárias do Google Classroom. Tarefas importadas com URL externa válida DEVEM disponibilizar abertura segura em nova aba.

#### Scenario: Tarefa sincronizada é exibida

- **WHEN** uma tarefa importada do Classroom é listada
- **THEN** ela mostra o selo Google Classroom e, se houver URL canônica, o link “Abrir no Classroom” com `noopener noreferrer`
