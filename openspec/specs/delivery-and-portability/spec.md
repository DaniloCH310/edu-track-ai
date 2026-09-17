# Capacidade: instalação, operação e reprodutibilidade

## Propósito

Permitir que o projeto seja instalado e executado em outra máquina Windows sem caminhos pessoais, permissões administrativas ou dependência de scripts PowerShell liberados globalmente.

## Requisitos

### Requirement: Inicialização portátil

`Instalar EduTrack.cmd` DEVE preparar ambiente Python, dependências e PostgreSQL portátil. `Iniciar EduTrack.cmd` DEVE iniciar banco, aplicar migrações e servir a aplicação em `127.0.0.1:8000`.

#### Scenario: Máquina sem Python compatível

- **WHEN** a instalação não encontra Python 3.12 ou superior
- **THEN** ela tenta instalar Python 3.12 para o usuário atual via `winget` e explica o endereço oficial caso o `winget` não esteja disponível

#### Scenario: Política restringe arquivos PS1

- **WHEN** o usuário abre o atalho `.cmd`
- **THEN** o atalho executa o PowerShell com política limitada ao próprio processo, sem pedir alteração permanente da política do Windows

### Requirement: Caminhos não dependem do computador do autor

Scripts e instruções de execução NÃO DEVEM conter caminho fixo de usuário. Eles DEVEM localizar o diretório do projeto pela própria posição.

#### Scenario: Projeto é extraído em outra pasta ou usuário Windows

- **WHEN** o usuário executa os atalhos na nova localização
- **THEN** instalação e início usam a pasta atual do projeto, sem edição de caminho

### Requirement: Evitar servidor ou interface antigos

O inicializador DEVE interromper a execução se a porta 8000 já estiver ocupada e DEVE validar os arquivos do Campus e da Agenda antes de subir. A API DEVE expor `/api/version` para diagnóstico da versão servida.

#### Scenario: Porta 8000 está em uso

- **WHEN** outro processo já ocupa `127.0.0.1:8000`
- **THEN** o inicializador mostra o conflito e não abre uma segunda instância enganosa

#### Scenario: Interface parece desatualizada

- **WHEN** o usuário executa `Diagnosticar EduTrack.cmd` com o servidor aberto
- **THEN** o diagnóstico compara a página servida com a identificação da API e confirma a presença de Campus e Agenda ou explica a divergência

### Requirement: Dados e segredos locais não são versionados

O Git DEVE ignorar `.env`, `.venv`, `.data` e `.tools`. O seed demonstrativo DEVE ser idempotente e não exibir senha no terminal.

#### Scenario: Repositório é enviado ao GitHub

- **WHEN** um desenvolvedor revisa o diff antes do commit
- **THEN** nenhuma credencial SMTP, segredo OAuth, token Classroom ou dado local do PostgreSQL está incluído
