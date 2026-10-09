$ErrorActionPreference = 'Stop'
$engineRoot = if ($env:UE_ENGINE_ROOT) { $env:UE_ENGINE_ROOT } else { 'E:\Epic Games\UE_5.8' }
$env:UV_CACHE_DIR = Join-Path $PSScriptRoot '.uv-cache'
uv sync --locked --project $PSScriptRoot --python "$engineRoot\Engine\Binaries\ThirdParty\Python3\Win64\python.exe"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& "$PSScriptRoot\.venv\Scripts\python.exe" -c "from mcp.server.fastmcp import FastMCP; print('MCP dependencies OK')"
exit $LASTEXITCODE
