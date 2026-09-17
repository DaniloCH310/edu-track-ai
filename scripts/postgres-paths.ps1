function Get-PostgresRuntimeRoot {
    param([Parameter(Mandatory)] [string] $ProjectRoot)

    if ($ProjectRoot -notmatch '[^\x00-\x7F]') {
        return $ProjectRoot
    }

    $toolsRoot = Join-Path $ProjectRoot '.tools'
    New-Item -ItemType Directory -Force -Path $toolsRoot | Out-Null
    $driveMarker = Join-Path $toolsRoot 'postgresql-drive.txt'
    $candidates = @()
    if (Test-Path -LiteralPath $driveMarker) {
        $saved = (Get-Content -Raw -LiteralPath $driveMarker).Trim().ToUpperInvariant()
        if ($saved -match '^[D-Z]:$') {
            $candidates += $saved
        }
    }
    $candidates += @('Z:', 'Y:', 'X:', 'W:', 'V:', 'U:', 'T:', 'S:', 'R:', 'Q:', 'P:')

    foreach ($drive in ($candidates | Select-Object -Unique)) {
        $driveRoot = "$drive\"
        if (Test-Path -LiteralPath $driveRoot) {
            $sameProject =
                (Test-Path -LiteralPath (Join-Path $driveRoot 'pyproject.toml')) -and
                (Test-Path -LiteralPath (Join-Path $driveRoot '.tools\postgresql'))
            if ($sameProject) {
                Set-Content -LiteralPath $driveMarker -Value $drive -Encoding ASCII
                return $driveRoot
            }
            continue
        }

        & subst.exe $drive $ProjectRoot
        if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $driveRoot)) {
            Set-Content -LiteralPath $driveMarker -Value $drive -Encoding ASCII
            return $driveRoot
        }
    }

    throw 'Não há uma letra de unidade livre para o PostgreSQL portátil.'
}

function New-PostgresStartupLogPath {
    param(
        [Parameter(Mandatory)] [string] $LogsRoot,
        [Parameter(Mandatory)] [string] $ClusterName
    )

    $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $attemptId = [Guid]::NewGuid().ToString('N').Substring(0, 8)
    return Join-Path $LogsRoot "$ClusterName-start-$timestamp-$PID-$attemptId.log"
}
