$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Write-Host "Pasta consultada: $projectRoot"
$expected = (Get-FileHash -LiteralPath (Join-Path $projectRoot 'app\static\index.html') -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Host "HTML local: $expected"
try {
    $version = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/version' -TimeoutSec 5
    Write-Host "Servidor: $($version.release) / $($version.interface)"
    Write-Host "HTML no servidor: $($version.html_sha256)"
    if ($version.html_sha256 -ne $expected) {
        throw 'O servidor esta usando arquivos diferentes desta pasta.'
    }
    $page = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8000/?diagnostico=campus2' -TimeoutSec 5
    if ($page.Content -notmatch 'id="learning-campus"' -or $page.Content -notmatch 'href="#agenda"') {
        throw 'O HTML recebido nao contem Campus e Agenda.'
    }
    Write-Host 'CONFIRMADO: servidor e pasta correspondem; HTML contem Campus e Agenda.'
    Write-Host 'Abra http://127.0.0.1:8000/?release=20260906-campus2 e pressione Ctrl+F5.'
} catch {
    Write-Host "DIAGNOSTICO: $($_.Exception.Message)"
    Write-Host 'Encerre o servidor antigo e use Iniciar EduTrack.cmd na pasta atualizada.'
}
