$ErrorActionPreference = 'Stop'
$rewardsPython = Join-Path $PSScriptRoot 'env\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $rewardsPython)) { throw 'Crea el entorno env e instala requirements.txt primero.' }
$env:DJANGO_DEBUG = '1'
$env:DJANGO_ALLOWED_HOSTS = 'localhost,127.0.0.1'
Push-Location (Join-Path $PSScriptRoot 'rewards')
try {
    & $rewardsPython manage.py check
    if ($LASTEXITCODE -ne 0) { throw 'Django encontró un problema de configuración.' }
    & $rewardsPython manage.py runserver 127.0.0.1:8000
} finally { Pop-Location }
