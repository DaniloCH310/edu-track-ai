[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$minimumPython = [Version]'3.12'

function Find-CompatiblePython {
    $candidates = [System.Collections.Generic.List[object]]::new()
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        foreach ($selector in @('-3.14', '-3.13', '-3.12', '-3')) {
            $candidates.Add([pscustomobject]@{
                Path = $launcher.Source
                Arguments = @($selector)
            })
        }
    }

    foreach ($commandName in @('python.exe', 'python3.exe')) {
        $command = Get-Command $commandName -ErrorAction SilentlyContinue
        if ($command) {
            $candidates.Add([pscustomobject]@{
                Path = $command.Source
                Arguments = @()
            })
        }
    }

    $localPythonRoot = Join-Path $env:LOCALAPPDATA 'Programs\Python'
    if (Test-Path -LiteralPath $localPythonRoot) {
        Get-ChildItem -LiteralPath $localPythonRoot -Filter python.exe -File -Recurse |
            Sort-Object FullName -Descending |
            ForEach-Object {
                $candidates.Add([pscustomobject]@{
                    Path = $_.FullName
                    Arguments = @()
                })
            }
    }

    foreach ($candidate in $candidates) {
        $executable = $candidate.Path
        $prefixArguments = $candidate.Arguments
        try {
            $versionText = & $executable @prefixArguments -c 'import platform; print(platform.python_version())' 2>$null
            if ($LASTEXITCODE -ne 0) {
                continue
            }
            $version = [Version](($versionText | Select-Object -Last 1).Trim())
            if ($version -ge $minimumPython) {
                return $candidate
            }
        } catch {
            continue
        }
    }
    return $null
}

function Install-CompatiblePython {
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw @'
Python 3.12 ou superior não foi encontrado e o Gerenciador de Pacotes do Windows (winget) não está disponível.
Instale o Python em https://www.python.org/downloads/windows/ marcando a opção "Add python.exe to PATH" e execute novamente "Instalar EduTrack.cmd".
'@
    }

    Write-Host 'Python compatível não encontrado. Instalando Python 3.12 somente para este usuário...'
    & $winget.Source install --id Python.Python.3.12 --exact --scope user --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        throw 'A instalação do Python 3.12 pelo winget falhou.'
    }

    $machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machinePath;$userPath"
}

$venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (Test-Path -LiteralPath $venvPython) {
    & $venvPython -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)'
    if ($LASTEXITCODE -ne 0) {
        throw 'A pasta .venv usa Python anterior ao 3.12. Renomeie essa pasta e execute novamente "Instalar EduTrack.cmd".'
    }
} else {
    $python = Find-CompatiblePython
    if (-not $python) {
        Install-CompatiblePython
        $python = Find-CompatiblePython
    }
    if (-not $python) {
        throw 'O Python 3.12 foi instalado, mas ainda não foi localizado. Feche esta janela e execute novamente "Instalar EduTrack.cmd".'
    }

    $pythonExecutable = $python.Path
    $pythonArguments = $python.Arguments
    Write-Host 'Criando o ambiente virtual do EduTrack...'
    & $pythonExecutable @pythonArguments -m venv $venvPython.Replace('\Scripts\python.exe', '')
    if ($LASTEXITCODE -ne 0) {
        throw 'Não foi possível criar o ambiente virtual.'
    }
}

Push-Location $projectRoot
try {
    Write-Host 'Instalando as dependências do EduTrack...'
    & $venvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        throw 'Não foi possível atualizar o pip.'
    }
    & $venvPython -m pip install -e ".[dev]"
    if ($LASTEXITCODE -ne 0) {
        throw 'Não foi possível instalar as dependências do EduTrack.'
    }

    if (-not (Test-Path -LiteralPath '.env')) {
        Copy-Item -LiteralPath '.env.example' -Destination '.env'
        Write-Host 'Arquivo .env criado a partir do modelo.'
    }

    & (Join-Path $PSScriptRoot 'setup-postgres.ps1')
    & $venvPython -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        throw 'A migração do banco falhou.'
    }
    & $venvPython -m scripts.seed
    if ($LASTEXITCODE -ne 0) {
        throw 'A criação dos dados iniciais falhou.'
    }
} finally {
    Pop-Location
}

Write-Host ''
Write-Host 'EduTrack instalado. Use "Iniciar EduTrack.cmd" para abrir o sistema.'
