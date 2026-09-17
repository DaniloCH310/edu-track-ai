[CmdletBinding()]
param(
    [ValidateSet('Dev', 'Test', 'All')]
    [string] $Cluster = 'All'
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'postgres-paths.ps1')
$runtimeProjectRoot = Get-PostgresRuntimeRoot -ProjectRoot $projectRoot
$rootMarker = Join-Path $projectRoot '.tools\postgresql-root.txt'
if (-not (Test-Path -LiteralPath $rootMarker)) {
    throw 'PostgreSQL portátil não encontrado. Execute .\scripts\setup-postgres.ps1.'
}

$pgCtlFile = Get-ChildItem -LiteralPath (Join-Path $runtimeProjectRoot '.tools\postgresql') -Filter pg_ctl.exe -File -Recurse | Select-Object -First 1
if (-not $pgCtlFile) {
    throw 'pg_ctl.exe não foi encontrado no pacote portátil.'
}
$postgresRoot = Split-Path -Parent (Split-Path -Parent $pgCtlFile.FullName)
$pgCtl = Join-Path $postgresRoot 'bin\pg_ctl.exe'
$pgIsReady = Join-Path $postgresRoot 'bin\pg_isready.exe'
$dataRoot = Join-Path $runtimeProjectRoot '.data\postgresql'
$logsRoot = Join-Path $dataRoot 'logs'
New-Item -ItemType Directory -Force -Path $logsRoot | Out-Null

$targets = if ($Cluster -eq 'All') { @('Dev', 'Test') } else { @($Cluster) }
Push-Location $runtimeProjectRoot
try {
foreach ($target in $targets) {
    $name = $target.ToLowerInvariant()
    $port = if ($name -eq 'dev') { 54329 } else { 54330 }
    $clusterPath = Join-Path $dataRoot $name
    if (-not (Test-Path -LiteralPath (Join-Path $clusterPath 'PG_VERSION'))) {
        throw "Cluster $name não inicializado. Execute .\scripts\setup-postgres.ps1."
    }

    & $pgCtl status -D $clusterPath *> $null
    if ($LASTEXITCODE -ne 0) {
        # Cada tentativa usa um arquivo próprio. No Windows, um processo órfão
        # pode manter o log anterior bloqueado após Ctrl+C.
        $logPath = New-PostgresStartupLogPath -LogsRoot $logsRoot -ClusterName $name
        & $pgCtl start -D $clusterPath -l $logPath -w
        if ($LASTEXITCODE -ne 0) {
            throw "Não foi possível iniciar o cluster $name. Consulte $logPath."
        }
    }

    & $pgIsReady -h 127.0.0.1 -p $port -t 10 *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "O cluster $name iniciou, mas não respondeu na porta $port."
    }
    Write-Host "PostgreSQL $name ativo em 127.0.0.1:$port."
}
} finally {
    Pop-Location
}
