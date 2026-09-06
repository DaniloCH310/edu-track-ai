[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $projectRoot '.env'
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$requiredFrontendFiles = @(
    'app\static\js\agenda.js',
    'app\static\css\campus.css',
    'app\static\assets\learning-campus.png'
)

if (-not (Test-Path -LiteralPath $envFile)) {
    throw 'Arquivo .env não encontrado. Copie .env.example para .env e configure o Gmail.'
}
if (-not (Test-Path -LiteralPath $python)) {
    throw 'Ambiente virtual não encontrado. Crie .venv e instale o projeto.'
}

$missingFrontendFiles = @(
    $requiredFrontendFiles | Where-Object {
        -not (Test-Path -LiteralPath (Join-Path $projectRoot $_))
    }
)
if ($missingFrontendFiles.Count -gt 0) {
    throw "Esta cópia do EduTrack está incompleta ou desatualizada. Arquivos ausentes: $($missingFrontendFiles -join ', '). Baixe novamente a branch main."
}

$portListener = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -First 1
if ($portListener) {
    throw "A porta 8000 já está em uso pelo processo $($portListener.OwningProcess). Feche a instância anterior do EduTrack antes de iniciar esta cópia; caso contrário, o navegador pode exibir uma versão antiga."
}

& (Join-Path $PSScriptRoot 'start-postgres.ps1') -Cluster Dev
Push-Location $projectRoot
try {
    & $python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        throw 'A migração do banco falhou.'
    }
    & $python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
} finally {
    Pop-Location
}
