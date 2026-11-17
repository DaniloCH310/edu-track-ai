# Capacidade: organização acadêmica

## Purpose

Permitir que o estudante organize disciplinas e tarefas próprias, enquanto preserva a origem de itens importados do Google Classroom.

## Requirements

### Requirement: Gestão de disciplinas

O sistema SHALL permitir criar, visualizar, editar e excluir disciplinas do próprio usuário. A disciplina pode conter nome, descrição, professor, período, carga horária e cor visual.

#### Scenario: Criação de uma disciplina

- **WHEN** o usuário registra uma disciplina válida
- **THEN** ela aparece na área Disciplinas e fica disponível para vincular tarefas

#### Scenario: Visualização em distrito acadêmico

- **WHEN** o usuário abre Disciplinas com registros existentes
- **THEN** cada disciplina aparece como um prédio/distrito com progresso, quantidade concluída e dados acadêmicos disponíveis

### Requirement: Gestão de tarefas

O sistema SHALL permitir criar, visualizar, editar, excluir e alterar o status de tarefas associadas a uma disciplina do usuário. Cada tarefa SHALL ter título, prazo e status; descrição é opcional.

#### Scenario: Alteração do status

- **WHEN** o usuário muda uma tarefa para `completed`
- **THEN** o progresso da disciplina e os indicadores dependentes são recalculados

#### Scenario: Lista de missões

- **WHEN** o usuário abre Tarefas
- **THEN** o sistema mostra tarefas como missões, com prazo, disciplina, estado e controles de edição/exclusão

### Requirement: Itens importados preservam sua origem

Disciplinas e tarefas importadas SHALL ser identificadas como originárias do Google Classroom. Tarefas importadas com URL externa válida SHALL disponibilizar abertura segura em nova aba.

#### Scenario: Tarefa sincronizada é exibida

- **WHEN** uma tarefa importada do Classroom é listada
- **THEN** ela mostra o selo Google Classroom e, se houver URL canônica, o link “Abrir no Classroom” com `noopener noreferrer`

### Requirement: Academic subject search

The system SHALL extend authenticated GET /api/subjects with optional query
(maximum 160 characters) and overdue (boolean, default false). query SHALL match
a literal case-insensitive substring of the subject name after trimming; empty
input SHALL disable the name filter. Percent and underscore SHALL be literal.
overdue=true SHALL require an existing non-completed task whose due_date is before
today in America/Sao_Paulo. Supplied filters SHALL combine with AND. Responses
SHALL retain the existing schema and alphabetical ordering, contain only owned
subjects and SHALL NOT duplicate subjects.

#### Scenario: Name search
- **WHEN** an authenticated student searches a name with different letter case
- **THEN** only their matching subjects are returned; an unknown name returns []

#### Scenario: Overdue boundaries
- **WHEN** overdue=true is supplied
- **THEN** subjects with one or many overdue pending/in-progress tasks appear once
- **AND** completed overdue tasks, tasks due today or later and subjects without tasks do not qualify

#### Scenario: Combined filters and privacy
- **WHEN** query and overdue=true are supplied
- **THEN** a subject must satisfy both filters and belong to the authenticated user

#### Scenario: Backward compatibility
- **WHEN** filters are omitted, or query is blank and overdue is false
- **THEN** the existing owned-subject list, ordering and response schema are preserved

#### Scenario: Invalid or unauthenticated request
- **WHEN** the query exceeds 160 characters or overdue is not a valid boolean
- **THEN** the API returns 422
- **AND** requests without a valid session remain unauthorized
