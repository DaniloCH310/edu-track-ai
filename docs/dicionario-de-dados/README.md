# Dicionário de dados do EduTrack

Este material apresenta as tabelas persistidas pelo EduTrack com base nos modelos SQLAlchemy atuais em `app/models/`. Cada print informa o campo, o tipo, a obrigatoriedade, as chaves ou regras e a finalidade na aplicação.

## Legenda

- **PK**: chave primária.
- **FK**: chave estrangeira.
- **UNIQUE**: valor ou combinação que não pode se repetir.
- **CASCADE**: a exclusão do registro pai remove o registro dependente.
- **SET NULL**: a exclusão do registro relacionado preserva este registro e limpa a referência.

## Tabelas

### 1. Usuários

![Dicionário da tabela users](prints/01_users.png)

### 2. Recuperação de senha

![Dicionário da tabela password_reset_tokens](prints/02_password_reset_tokens.png)

### 3. Disciplinas

![Dicionário da tabela subjects](prints/03_subjects.png)

### 4. Tarefas acadêmicas

![Dicionário da tabela academic_tasks](prints/04_academic_tasks.png)

### 5. Conversas da EDU IA

![Dicionário da tabela edu_ai_conversations](prints/05_edu_ai_conversations.png)

### 6. Mensagens da EDU IA

![Dicionário da tabela edu_ai_messages](prints/06_edu_ai_messages.png)

### 7. Missões de revisão

![Dicionário da tabela review_missions](prints/07_review_missions.png)

### 8. Conexões Google Classroom

![Dicionário da tabela private.classroom_connections](prints/08_classroom_connections.png)

### 9. Vínculos de turmas Google Classroom

![Dicionário da tabela private.classroom_course_links](prints/09_classroom_course_links.png)

### 10. Vínculos de tarefas Google Classroom

![Dicionário da tabela private.classroom_task_links](prints/10_classroom_task_links.png)

## Relações principais

- Um usuário possui várias disciplinas.
- Uma disciplina possui várias tarefas.
- Uma tarefa pode gerar uma missão de revisão.
- Uma conversa da EDU IA possui várias mensagens e pode referenciar uma disciplina ou tarefa.
- Uma conexão do Google Classroom possui vínculos de turmas, e cada vínculo de turma possui vínculos de tarefas.

Os valores de hashes, tokens de recuperação e tokens criptografados não devem ser exibidos na apresentação. Mostre somente as definições dos campos.
