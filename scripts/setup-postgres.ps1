[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'postgres-paths.ps1')
$runtimeProjectRoot = Get-PostgresRuntimeRoot -ProjectRoot $projectRoot
$toolsRoot = Join-Path $projectRoot '.tools'
$downloadsRoot = Join-Path $toolsRoot 'downloads'
$extractRoot = Join-Path $toolsRoot 'postgresql'
$rootMarker = Join-Path $toolsRoot 'postgresql-root.txt'
$archivePath = Join-Path $downloadsRoot 'postgresql-16.15-windows-x64.zip'
$downloadUrl = 'https://sbp.enterprisedb.com/getfile.jsp?fileid=1260422'
$runtimeExtractRoot = Join-Path $runtimeProjectRoot '.tools\postgresql'
$dataRoot = Join-Path $runtimeProjectRoot '.data\postgresql'

New-Item -ItemType Directory -Force -Path $downloadsRoot, $extractRoot, $dataRoot | Out-Null

$minimumArchiveSize = 300MB
$archiveLength = if (Test-Path -LiteralPath $archivePath) {
    (Get-Item -LiteralPath $archivePath).Length
} else {
    0
}
if ($archiveLength -lt $minimumArchiveSize) {
    Write-Host 'Baixando PostgreSQL 16.15 portátil (aprox. 320 MB, com retomada)...'
    $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if ($curl) {
        & $curl.Source -L --fail --retry 5 --continue-at - --output $archivePath $downloadUrl
        if ($LASTEXITCODE -ne 0) {
            throw 'O download do PostgreSQL falhou.'
        }
    } else {
        Invoke-WebRequest -UseBasicParsing -Uri $downloadUrl -OutFile $archivePath
    }
}

$archive = Get-Item -LiteralPath $archivePath
if ($archive.Length -lt $minimumArchiveSize) {
    throw "O arquivo baixado é menor que o esperado: $archivePath"
}

$stream = [System.IO.File]::OpenRead($archivePath)
try {
    $first = $stream.ReadByte()
    $second = $stream.ReadByte()
} finally {
    $stream.Dispose()
}
if ($first -ne 0x50 -or $second -ne 0x4B) {
    throw "O download não possui assinatura ZIP válida: $archivePath"
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($archivePath)
try {
    if (-not ($zip.Entries | Where-Object { $_.FullName -match '(^|/)bin/initdb\.exe$' })) {
        throw 'O arquivo ZIP não contém bin/initdb.exe.'
    }
} finally {
    $zip.Dispose()
}

$initdb = Get-ChildItem -LiteralPath $runtimeExtractRoot -Filter initdb.exe -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $initdb) {
    Write-Host 'Extraindo PostgreSQL portátil...'
    $tar = Get-Command tar.exe -ErrorAction SilentlyContinue
    if ($tar) {
        & $tar.Source -xf $archivePath -C $extractRoot
        if ($LASTEXITCODE -ne 0) {
            throw 'A extraÃ§Ã£o do PostgreSQL falhou.'
        }
    } else {
        Expand-Archive -LiteralPath $archivePath -DestinationPath $extractRoot -Force
    }
    $initdb = Get-ChildItem -LiteralPath $runtimeExtractRoot -Filter initdb.exe -File -Recurse | Select-Object -First 1
}
if (-not $initdb) {
    throw 'initdb.exe não foi encontrado após a extração.'
}

$postgresRoot = Split-Path -Parent (Split-Path -Parent $initdb.FullName)
Set-Content -LiteralPath $rootMarker -Value $postgresRoot -Encoding UTF8

function Initialize-Cluster {
    param(
        [Parameter(Mandatory)] [string] $Name,
        [Parameter(Mandatory)] [int] $Port,
        [Parameter(Mandatory)] [string] $Password
    )

    $clusterPath = Join-Path $dataRoot $Name
    $versionFile = Join-Path $clusterPath 'PG_VERSION'
    if (Test-Path -LiteralPath $versionFile) {
        Write-Host "Cluster $Name já inicializado."
        return
    }

    New-Item -ItemType Directory -Force -Path $clusterPath | Out-Null
    $passwordFile = Join-Path $dataRoot ".$Name-password.tmp"
    Set-Content -LiteralPath $passwordFile -Value $Password -NoNewline -Encoding ASCII
    try {
        & $initdb.FullName -D $clusterPath -U edutrack -A scram-sha-256 "--pwfile=$passwordFile" --encoding=UTF8 --locale=C
        if ($LASTEXITCODE -ne 0) {
            throw "initdb falhou para o cluster $Name."
        }
    } finally {
        Remove-Item -LiteralPath $passwordFile -Force -ErrorAction SilentlyContinue
    }

    $configuration = @"

# EduTrack local configuration
listen_addresses = '127.0.0.1'
port = $Port
max_connections = 50
shared_buffers = 64MB
"@
    Add-Content -LiteralPath (Join-Path $clusterPath 'postgresql.conf') -Value $configuration -Encoding UTF8
}

Push-Location $runtimeProjectRoot
try {
    Initialize-Cluster -Name 'dev' -Port 54329 -Password 'edutrack_local'
    Initialize-Cluster -Name 'test' -Port 54330 -Password 'edutrack_test'
} finally {
    Pop-Location
}

& (Join-Path $PSScriptRoot 'start-postgres.ps1') -Cluster All

$psql = Join-Path $postgresRoot 'bin\psql.exe'
$createdb = Join-Path $postgresRoot 'bin\createdb.exe'
function Ensure-Database {
    param(
        [Parameter(Mandatory)] [int] $Port,
        [Parameter(Mandatory)] [string] $Password,
        [Parameter(Mandatory)] [string] $Database
    )
    $previousPassword = $env:PGPASSWORD
    $env:PGPASSWORD = $Password
    try {
        $exists = & $psql -h 127.0.0.1 -p $Port -U edutrack -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$Database'"
        if ($LASTEXITCODE -ne 0) {
            throw "Não foi possível consultar o cluster na porta $Port."
        }
        if (($exists | Out-String).Trim() -ne '1') {
            & $createdb -h 127.0.0.1 -p $Port -U edutrack $Database
            if ($LASTEXITCODE -ne 0) {
                throw "Não foi possível criar o banco $Database."
            }
        }
    } finally {
        if ($null -eq $previousPassword) {
            Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
        } else {
            $env:PGPASSWORD = $previousPassword
        }
    }
}

Ensure-Database -Port 54329 -Password 'edutrack_local' -Database 'edutrack'
Ensure-Database -Port 54330 -Password 'edutrack_test' -Database 'edutrack_test'
Write-Host 'PostgreSQL portátil configurado e pronto.'
