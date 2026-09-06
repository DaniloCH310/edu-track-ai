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
    Write-Host "EduTrack Campus - pasta: $projectRoot"
    & $python -c 'import app, sys; from pathlib import Path; actual = Path(app.__file__).resolve(); print(actual); raise SystemExit(0 if actual == Path(sys.argv[1]).resolve() else 1)' (Join-Path $projectRoot 'app\__init__.py')
    if ($LASTEXITCODE -ne 0) {
        throw 'O Python carregou outra instalacao. Execute Instalar EduTrack.cmd nesta pasta.'
    }
    & $python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        throw 'A migração do banco falhou.'
    }
    Write-Host 'Abra http://127.0.0.1:8000/?release=20260906-campus2'
    & $python -m uvicorn app.main:app --app-dir $projectRoot --host 127.0.0.1 --port 8000
    if ($LASTEXITCODE -ne 0) {
        throw 'O servidor nao iniciou corretamente. Consulte a mensagem acima.'
    }
} finally {
    Pop-Location
}
