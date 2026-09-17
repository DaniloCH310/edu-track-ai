# Capacidade: EDU IA

## Propósito

Oferecer um tutor acadêmico por texto que ajuda o estudante a entender conteúdos e iniciar tarefas dentro do contexto do seu Campus.

## Requisitos

### Requirement: Tutor contextual e privado

O EDU IA DEVE permitir conversas privadas por usuário. Uma conversa pode ser geral ou vinculada a uma disciplina ou tarefa do próprio usuário; a resposta usa somente o contexto acadêmico vinculado e as mensagens recentes da conversa.

#### Scenario: Dúvida em uma tarefa

- **WHEN** o estudante abre EDU IA a partir de uma tarefa própria e envia uma pergunta
- **THEN** o tutor recebe título, descrição, disciplina e mensagens recentes, responde em português do Brasil e salva pergunta e resposta na conversa

#### Scenario: Tentativa de usar contexto de outro estudante

- **WHEN** uma pessoa tenta criar conversa com identificador de disciplina ou tarefa que não lhe pertence
- **THEN** o sistema informa que o recurso não foi encontrado e não revela dados do proprietário

### Requirement: Histórico controlado pelo estudante

O estudante DEVE poder listar, retomar e excluir suas conversas. Excluir uma conversa DEVE remover todas as mensagens dela.

#### Scenario: Exclusão de conversa

- **WHEN** o estudante confirma a exclusão de uma conversa própria
- **THEN** a conversa deixa de aparecer no histórico e suas mensagens são removidas

### Requirement: Provedor opcional e limites de demonstração

O EDU IA DEVE ficar indisponível quando a chave Gemini não estiver configurada, sem afetar as demais áreas do EduTrack. Quando habilitado, o sistema DEVE limitar cada usuário a cinco perguntas por minuto e cinquenta em 24 horas, salvo configuração do ambiente.

#### Scenario: Provedor indisponível

- **WHEN** o Gemini não está configurado ou falha temporariamente
- **THEN** a interface informa indisponibilidade sem expor chaves, e uma pergunta já salva permanece no histórico

### Requirement: Uso educativo responsável

O tutor DEVE orientar o raciocínio e declarar incerteza quando necessário. A interface DEVE informar que a demonstração não é apropriada para dados pessoais ou respostas completas de avaliações.
