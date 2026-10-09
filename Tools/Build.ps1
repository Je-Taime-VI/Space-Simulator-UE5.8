param([switch]$GenerateProjectFiles)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$engineRoot = if ($env:UE_ENGINE_ROOT) { $env:UE_ENGINE_ROOT } else { 'E:\Epic Games\UE_5.8' }
$projectFile = Join-Path $projectRoot 'BigWorld.uproject'
if ($GenerateProjectFiles) {
    & "$engineRoot\Engine\Build\BatchFiles\Build.bat" -projectfiles "-project=$projectFile" -game -engine -2022
} else {
    & "$engineRoot\Engine\Build\BatchFiles\Build.bat" BigWorldEditor Win64 Development "-Project=$projectFile" -WaitMutex "-Log=$projectRoot\Saved\Logs\BuildEditor.log"
}
exit $LASTEXITCODE
