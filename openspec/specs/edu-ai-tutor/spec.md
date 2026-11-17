# Capacidade: EDU IA

## Purpose

Oferecer um tutor acadêmico por texto que ajuda o estudante a entender conteúdos e iniciar tarefas dentro do contexto do seu Campus.

## Requirements

### Requirement: Tutor contextual e privado

O EDU IA SHALL permitir conversas privadas por usuário. Uma conversa pode ser geral ou vinculada a uma disciplina ou tarefa do próprio usuário; a resposta usa somente o contexto acadêmico vinculado e as mensagens recentes da conversa.

#### Scenario: Dúvida em uma tarefa

- **WHEN** o estudante abre EDU IA a partir de uma tarefa própria e envia uma pergunta
- **THEN** o tutor recebe título, descrição, disciplina e mensagens recentes, responde em português do Brasil e salva pergunta e resposta na conversa

#### Scenario: Tentativa de usar contexto de outro estudante

- **WHEN** uma pessoa tenta criar conversa com identificador de disciplina ou tarefa que não lhe pertence
- **THEN** o sistema informa que o recurso não foi encontrado e não revela dados do proprietário

### Requirement: Histórico controlado pelo estudante

O estudante SHALL poder listar, retomar e excluir suas conversas. Excluir uma conversa SHALL remover todas as mensagens dela.

#### Scenario: Exclusão de conversa

- **WHEN** o estudante confirma a exclusão de uma conversa própria
- **THEN** a conversa deixa de aparecer no histórico e suas mensagens são removidas

### Requirement: Provedor opcional e limites de demonstração

O EDU IA SHALL ficar indisponível quando a chave Gemini não estiver configurada, sem afetar as demais áreas do EduTrack. Quando habilitado, o sistema SHALL limitar cada usuário a cinco perguntas por minuto e cinquenta em 24 horas, salvo configuração do ambiente.

#### Scenario: Provedor indisponível

- **WHEN** o Gemini não está configurado ou falha temporariamente
- **THEN** a interface informa indisponibilidade sem expor chaves, e uma pergunta já salva permanece no histórico

### Requirement: Uso educativo responsável

O tutor SHALL orientar o raciocínio e declarar incerteza quando necessário. A interface SHALL informar que a demonstração não é apropriada para dados pessoais ou respostas completas de avaliações.

#### Scenario: Orientação antes de enviar conteúdo

- **WHEN** o estudante abre a área do EDU IA
- **THEN** a interface apresenta o aviso de uso educativo e de não envio de dados pessoais ou avaliações completas

### Requirement: Orçamento compartilhado e revisões idempotentes

Chat, geração de perguntas e avaliação de revisões SHALL compartilhar reservas
por usuário de 5 chamadas/minuto e 50/24 horas por processo, configuráveis. Falhas
do provedor SHALL consumir a reserva. A contagem persistente de mensagens do chat
SHALL continuar sendo aplicada. A memória SHALL ter capacidade limitada; esses
contadores não são compartilhados entre instâncias nem sobrevivem a reinícios.

#### Scenario: Orçamento esgotado

- **WHEN** uma chamada externa excederia o orçamento aplicável
- **THEN** a API SHALL retornar 429 com `Retry-After` antes de chamar Gemini

#### Scenario: Repetição ou concorrência na revisão

- **WHEN** uma revisão concluída recebe nova submissão
- **THEN** o resultado histórico SHALL ser devolvido sem chamar Gemini nem substituir respostas
- **AND** início/submissão SHALL adquirir lock da revisão do usuário na transação; disputa de lock SHALL retornar 409 com espera

#### Scenario: Avaliação indisponível

- **WHEN** o Gemini falha durante uma avaliação autorizada
- **THEN** as respostas SHALL ser preservadas com nota nula e aviso de avaliação indisponível
- **AND** repetir a submissão SHALL NOT gerar outra avaliação automaticamente
