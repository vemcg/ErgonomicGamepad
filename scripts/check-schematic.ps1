param(
	[string]$SchematicPath = "",
	[string]$ReportPath = "jlcpcb/production_files/erc-report.rpt"
)

$ErrorActionPreference = "Stop"

function Resolve-KiCadCli {
	$cmd = Get-Command kicad-cli -ErrorAction SilentlyContinue
	if ($cmd) {
		return $cmd.Source
	}

	$defaultPath = "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
	if (Test-Path $defaultPath) {
		return $defaultPath
	}

	throw "kicad-cli.exe not found. Install KiCad or add KiCad bin to PATH."
}

function Resolve-SchematicPath([string]$RequestedPath) {
	if (-not [string]::IsNullOrWhiteSpace($RequestedPath)) {
		if (Test-Path $RequestedPath) {
			return $RequestedPath
		}

		throw "Schematic file not found: $RequestedPath"
	}

	$candidates = @(
		"ErgonomicGamepad.sch",
		"ErgonomicGamepad.kicad_sch",
		"Ready to Fill ErgonomicGamepad.kicad_sch"
	)

	foreach ($candidate in $candidates) {
		if (Test-Path $candidate) {
			return $candidate
		}
	}

	throw "Could not find a schematic file automatically. Pass -SchematicPath explicitly."
}

$schematic = Resolve-SchematicPath $SchematicPath
$kicadCli = Resolve-KiCadCli
$reportDir = Split-Path -Parent $ReportPath

if ($reportDir -and -not (Test-Path $reportDir)) {
	New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
}

Write-Host "Using KiCad CLI: $kicadCli"
Write-Host "Checking schematic: $schematic"
Write-Host "ERC report: $ReportPath"

& $kicadCli sch erc "$schematic" --output "$ReportPath"
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
	Write-Host "KiCad loaded the schematic and completed ERC."
	exit 0
}

Write-Error "KiCad ERC failed with exit code $exitCode. See report: $ReportPath"
exit $exitCode
