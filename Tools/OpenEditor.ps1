$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$engineRoot = if ($env:UE_ENGINE_ROOT) { $env:UE_ENGINE_ROOT } else { 'E:\Epic Games\UE_5.8' }
# This explicitly opens the interactive editor requested by the project workflow.
Start-Process -FilePath "$engineRoot\Engine\Binaries\Win64\UnrealEditor.exe" -ArgumentList ('"' + (Join-Path $projectRoot 'BigWorld.uproject') + '"')
