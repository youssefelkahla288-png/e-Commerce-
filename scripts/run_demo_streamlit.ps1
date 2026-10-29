$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$demoDatabase = Join-Path $projectRoot "data\demo_ecommerce.db"
$streamlitApp = Join-Path $projectRoot "streamlit_app.py"
$python = "C:\Users\Youssef\venvs\ecommerce-py312\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Python 3.12 interpreter not found: $python"
}
if (-not (Test-Path -LiteralPath $demoDatabase -PathType Leaf)) {
    throw "Demo database not found; this launcher does not create it: $demoDatabase"
}

$previousDatabasePath = $env:ECOMMERCE_DB_PATH
Push-Location $projectRoot
try {
    # Set this before Python imports app.config and Streamlit imports the app.
    $env:ECOMMERCE_DB_PATH = (Resolve-Path -LiteralPath $demoDatabase).Path
    & $python -m streamlit run $streamlitApp
    if ($LASTEXITCODE -ne 0) {
        throw "Streamlit exited with code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
    if ($null -eq $previousDatabasePath) {
        Remove-Item Env:ECOMMERCE_DB_PATH -ErrorAction SilentlyContinue
    }
    else {
        $env:ECOMMERCE_DB_PATH = $previousDatabasePath
    }
}
