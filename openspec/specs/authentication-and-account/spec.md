# Capacidade: autenticação e conta

## Propósito

Permitir acesso seguro e individual ao EduTrack, com criação de conta, sessão, encerramento de sessão e recuperação de senha por Gmail configurado.

## Requisitos

### Requirement: Cadastro e acesso individual

O sistema DEVE permitir que uma pessoa crie uma conta e entre com e-mail e senha. Dados acadêmicos retornados pela API DEVEM pertencer apenas ao usuário autenticado.

#### Scenario: Usuário entra com credenciais válidas

- **WHEN** o usuário envia e-mail e senha válidos
- **THEN** o sistema cria a sessão e abre o dashboard desse usuário

#### Scenario: Credenciais inválidas

- **WHEN** o usuário envia uma senha incorreta ou um e-mail não cadastrado
- **THEN** o sistema recusa o acesso sem revelar qual campo está incorreto

### Requirement: Senhas permanecem protegidas e conferíveis durante o preenchimento

Senhas DEVEM ser armazenadas com hash Argon2. Os campos de senha DEVEM iniciar ocultos e oferecer um controle acessível para mostrar ou ocultar o valor digitado, sem alterar o valor nem enviá-lo ao servidor.

#### Scenario: Usuário consulta a senha antes de entrar

- **WHEN** o usuário aciona o controle de visualização no campo de senha
- **THEN** o campo alterna entre `password` e `text`, com rótulo que descreve a próxima ação

### Requirement: Recuperação de senha por e-mail

Quando Gmail SMTP estiver configurado, o sistema DEVE permitir solicitar redefinição de senha por link temporário. A resposta ao pedido DEVE ser neutra, para não confirmar se um e-mail possui conta.

#### Scenario: E-mail cadastrado solicita recuperação

- **WHEN** o usuário solicita recuperação para uma conta existente
- **THEN** o sistema envia um link de uso temporário para o e-mail configurado e mantém a mesma resposta pública da solicitação inexistente

#### Scenario: E-mail não cadastrado solicita recuperação

- **WHEN** o usuário solicita recuperação para um e-mail sem conta
- **THEN** o sistema não envia senha nem confirma a inexistência da conta

### Requirement: Encerramento de sessão

O sistema DEVE oferecer saída explícita e invalidar a sessão no navegador.

#### Scenario: Usuário seleciona Sair

- **WHEN** o usuário seleciona a ação de saída
- **THEN** as telas protegidas voltam a exigir autenticação
