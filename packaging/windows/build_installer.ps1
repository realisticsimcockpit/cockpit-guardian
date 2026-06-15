param(
    [switch]$SkipInstaller,
    [switch]$DeepClean
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$BuildRoot = Join-Path $RepoRoot "build\windows"
$NuitkaRoot = Join-Path $BuildRoot "nuitka"
$StageDir = Join-Path $BuildRoot "CockpitGuardian"
$DistDir = Join-Path $RepoRoot "dist"

function Find-Iscc {
    $cmd = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $candidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 7\ISCC.exe",
        "${env:ProgramFiles}\Inno Setup 7\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
    )
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }
    return $null
}

Set-Location $RepoRoot

if ($DeepClean) {
    Remove-Item $BuildRoot, $DistDir -Recurse -Force -ErrorAction SilentlyContinue
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    python -m venv .venv
}

$Python = Resolve-Path ".venv\Scripts\python.exe"
& $Python -m pip install --upgrade pip
& $Python -m pip install -e ".[windows,build]"
$Version = (& $Python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])").Trim()
$Publisher = "Realistic SimCockpit / Julien Merelle"
$ProductName = "Cockpit Guardian"
Write-Host "Building $ProductName $Version"

Remove-Item $NuitkaRoot, $StageDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $NuitkaRoot, $StageDir, $DistDir | Out-Null

$nuitkaArgs = @(
    "-m", "nuitka",
    "--mode=standalone",
    "--enable-plugin=pyside6",
    "--windows-console-mode=disable",
    "--assume-yes-for-downloads",
    "--remove-output",
    "--output-dir=$NuitkaRoot",
    "--output-filename=CockpitGuardian.exe",
    "--windows-icon-from-ico=src\cockpit_guardian\assets\app_icon.ico",
    "--include-data-dir=src\cockpit_guardian\assets=cockpit_guardian\assets",
    "--windows-company-name=$Publisher",
    "--windows-product-name=$ProductName",
    "--windows-file-description=$ProductName",
    "--windows-file-version=$Version",
    "--windows-product-version=$Version",
    "--copyright=Copyright (c) 2026 $Publisher",
    "--nofollow-import-to=pytest,unittest,tkinter",
    "--python-flag=-m",
    "src\cockpit_guardian"
)

& $Python @nuitkaArgs

$distCandidates = Get-ChildItem $NuitkaRoot -Directory -Filter "*.dist"
if ($distCandidates.Count -ne 1) {
    throw "Expected exactly one Nuitka .dist directory in $NuitkaRoot, found $($distCandidates.Count)."
}

Copy-Item (Join-Path $distCandidates[0].FullName "*") $StageDir -Recurse -Force
Copy-Item "README.md" $StageDir -Force
Copy-Item "LICENSE" $StageDir -Force
Copy-Item "CHANGELOG.md" $StageDir -Force
Copy-Item "docs" (Join-Path $StageDir "docs") -Recurse -Force
Copy-Item "src\cockpit_guardian\assets\app_icon.ico" $StageDir -Force

if ($SkipInstaller) {
    Write-Host "Standalone application staged in: $StageDir"
    exit 0
}

$Iscc = Find-Iscc
if (-not $Iscc) {
    Write-Host "Standalone application staged in: $StageDir"
    Write-Host "Inno Setup compiler ISCC.exe was not found. Install Inno Setup 7 or add ISCC.exe to PATH, then rerun without -SkipInstaller."
    exit 2
}

$Iss = Join-Path $PSScriptRoot "CockpitGuardian.iss"
& $Iscc "/DSourceDir=$StageDir" "/DOutputDir=$DistDir" "/DMyAppVersion=$Version" $Iss
Write-Host "Installer output directory: $DistDir"
