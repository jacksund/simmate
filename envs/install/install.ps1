# Installs uv (if needed) and then Simmate as a uv tool:
#   powershell -ExecutionPolicy ByPass -c "irm https://simmate.org/install.ps1 | iex"
$ErrorActionPreference = "Stop"

# uv's installer adds itself to PATH for new terminals only, so we call it
# from its default install location instead
if (Get-Command uv -ErrorAction SilentlyContinue) {
    $uv = "uv"
} else {
    Write-Host "Installing uv..."
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    if ($LASTEXITCODE -ne 0) { throw "Failed to install uv" }
    $uv = "$HOME\.local\bin\uv.exe"
}

Write-Host "Installing Simmate..."
& $uv tool install --upgrade --python 3.13 "simmate[all]"
if ($LASTEXITCODE -ne 0) { throw "Failed to install Simmate" }
# uv already warns about PATH above, so a failure here shouldn't stop the install
& $uv tool update-shell

Write-Host @"

Simmate is installed! Restart your terminal, then run:
    simmate --help

To import simmate in your own Python scripts (or Spyder), create a virtual
environment instead:
    https://jacksund.github.io/simmate/getting_started/installation/create_your_env/
"@
