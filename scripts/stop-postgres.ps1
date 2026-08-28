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
    Write-Host 'PostgreSQL portátil ainda não foi configurado.'
    exit 0
}

$pgCtlFile = Get-ChildItem -LiteralPath (Join-Path $runtimeProjectRoot '.tools\postgresql') -Filter pg_ctl.exe -File -Recurse | Select-Object -First 1
if (-not $pgCtlFile) {
    throw 'pg_ctl.exe não foi encontrado no pacote portátil.'
}
$postgresRoot = Split-Path -Parent (Split-Path -Parent $pgCtlFile.FullName)
$pgCtl = Join-Path $postgresRoot 'bin\pg_ctl.exe'
$dataRoot = Join-Path $runtimeProjectRoot '.data\postgresql'
$targets = if ($Cluster -eq 'All') { @('Dev', 'Test') } else { @($Cluster) }

Push-Location $runtimeProjectRoot
try {
foreach ($target in $targets) {
    $name = $target.ToLowerInvariant()
    $clusterPath = Join-Path $dataRoot $name
    if (-not (Test-Path -LiteralPath (Join-Path $clusterPath 'PG_VERSION'))) {
        continue
    }
    & $pgCtl status -D $clusterPath *> $null
    if ($LASTEXITCODE -eq 0) {
        & $pgCtl stop -D $clusterPath -m fast -w
        if ($LASTEXITCODE -ne 0) {
            throw "Não foi possível encerrar o cluster $name."
        }
        Write-Host "PostgreSQL $name encerrado."
    }
}
} finally {
    Pop-Location
}
