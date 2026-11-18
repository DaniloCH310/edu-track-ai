# Capacidade: autenticação e conta

## Purpose

Permitir acesso seguro e individual ao EduTrack, com criação de conta, sessão, encerramento de sessão e recuperação de senha por Gmail configurado.

## Requirements

### Requirement: Cadastro e acesso individual

O sistema SHALL permitir que uma pessoa crie uma conta e entre com e-mail e senha. Dados acadêmicos retornados pela API SHALL pertencer apenas ao usuário autenticado.

#### Scenario: Usuário entra com credenciais válidas

- **WHEN** o usuário envia e-mail e senha válidos
- **THEN** o sistema cria a sessão e abre o dashboard desse usuário

#### Scenario: Credenciais inválidas

- **WHEN** o usuário envia uma senha incorreta ou um e-mail não cadastrado
- **THEN** o sistema recusa o acesso sem revelar qual campo está incorreto

### Requirement: Senhas permanecem protegidas e conferíveis durante o preenchimento

Senhas SHALL ser armazenadas com hash Argon2. Os campos de senha SHALL iniciar ocultos e oferecer um controle acessível para mostrar ou ocultar o valor digitado, sem alterar o valor nem enviá-lo ao servidor.

#### Scenario: Usuário consulta a senha antes de entrar

- **WHEN** o usuário aciona o controle de visualização no campo de senha
- **THEN** o campo alterna entre `password` e `text`, com rótulo que descreve a próxima ação

### Requirement: Recuperação de senha por e-mail

Quando Gmail SMTP estiver configurado, o sistema SHALL permitir solicitar redefinição de senha por link temporário. A resposta ao pedido SHALL ser neutra, para não confirmar se um e-mail possui conta.

#### Scenario: E-mail cadastrado solicita recuperação

- **WHEN** o usuário solicita recuperação para uma conta existente
- **THEN** o sistema envia um link de uso temporário para o e-mail configurado e mantém a mesma resposta pública da solicitação inexistente

#### Scenario: E-mail não cadastrado solicita recuperação

- **WHEN** o usuário solicita recuperação para um e-mail sem conta
- **THEN** o sistema não envia senha nem confirma a inexistência da conta

#### Scenario: Falha ou timeout no SMTP

- **WHEN** a conexão, negociação TLS, autenticação, envio ou encerramento SMTP falha durante a recuperação
- **THEN** a API SHALL manter o status 202 e a mesma mensagem neutra usada para e-mails não cadastrados
- **AND** SHALL desfazer a criação do novo token e a invalidação dos anteriores
- **AND** SHALL registrar um aviso interno sem e-mail, token, senha, credenciais ou texto da exceção
- **AND** a conexão e as operações de socket SMTP SHALL usar timeout explícito de 10 segundos por operação

#### Scenario: Token temporário de uso único

- **WHEN** um link de recuperação é enviado com sucesso
- **THEN** somente o hash do token SHALL ser persistido com a expiração configurada
- **AND** tokens expirados ou já utilizados SHALL ser recusados

### Requirement: Encerramento de sessão

O sistema SHALL oferecer saída explícita e invalidar a sessão no navegador.

#### Scenario: Usuário seleciona Sair

- **WHEN** o usuário seleciona a ação de saída
- **THEN** as telas protegidas voltam a exigir autenticação
