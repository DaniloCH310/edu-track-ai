# Capacidade: integração Google Classroom

## Propósito

Permitir importação manual e somente leitura de turmas e atividades com prazo do Google Classroom para o Campus do estudante.

## Requisitos

### Requirement: Integração é opcional e explícita

O Classroom DEVE iniciar desabilitado até que as variáveis OAuth sejam configuradas. Quando indisponível, a aplicação continua operando com cadastro manual de disciplinas e tarefas.

#### Scenario: Ambiente sem credenciais Google

- **WHEN** `GOOGLE_CLASSROOM_ENABLED=false`
- **THEN** a aplicação inicia normalmente e a interface informa que a integração ainda não está configurada

### Requirement: Autorização individual e protegida

O backend DEVE executar OAuth Authorization Code com PKCE para a sessão EduTrack atual. Estado e verificador DEVEM expirar em dez minutos e ficar em cookie `HttpOnly`; tokens não podem ser encaminhados ao frontend ou à URL.

#### Scenario: Usuário autoriza o aplicativo

- **WHEN** o Google retorna um código e um estado válidos para a sessão atual
- **THEN** o backend cifra e persiste apenas o refresh token, registra os escopos e devolve o usuário à área Integrações

#### Scenario: Instituição bloqueia o aplicativo

- **WHEN** o Google retorna política administrativa ou escopos insuficientes
- **THEN** a interface informa que a instituição precisa liberar o acesso, sem tentar contornar a política

### Requirement: Importação é somente leitura e idempotente

A sincronização manual DEVE importar apenas cursos ativos visíveis ao estudante e atividades publicadas com prazo. Sincronizações idênticas NÃO DEVEM duplicar disciplinas ou tarefas.

#### Scenario: Sincronismo repetido

- **WHEN** o usuário executa duas sincronizações sem alteração no Classroom
- **THEN** a segunda execução não cria registros duplicados

#### Scenario: Atividade sem prazo

- **WHEN** uma atividade do Classroom não tem `dueDate` válido
- **THEN** o sistema a ignora, contabiliza o aviso sanitizado e mantém as demais atividades processáveis

### Requirement: O EduTrack não escreve no Classroom

O sistema NÃO DEVE criar, editar, excluir ou entregar atividades no Google Classroom. Os únicos escopos solicitados são leitura de cursos e leitura das atividades do próprio estudante.

#### Scenario: Usuário sincroniza atividades

- **WHEN** a sincronização é concluída
- **THEN** as tarefas aparecem no EduTrack, mas nenhuma atividade, entrega, nota ou anexo é alterado no Google

### Requirement: Desconexão preserva o histórico acadêmico local

Ao desconectar, o sistema DEVE remover token e vínculos de integração, mas DEVE manter disciplinas e tarefas já importadas.

#### Scenario: Usuário desconecta a conta Google

- **WHEN** o usuário confirma a desconexão
- **THEN** uma nova sincronização exige reconexão, enquanto os itens já trazidos seguem visíveis no EduTrack
