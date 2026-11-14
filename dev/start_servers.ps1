<#
Laptop only, Windows: the same as dev/start_servers.sh. Builds llama.cpp at the pinned
commit (CPU only), downloads the two models and checks their SHA256, and starts both
llama-servers with the board's flags and ports.

    powershell -ExecutionPolicy Bypass -File dev\start_servers.ps1
    powershell -ExecutionPolicy Bypass -File dev\start_servers.ps1 -Stop
    powershell -ExecutionPolicy Bypass -File dev\start_servers.ps1 -Status

Needs git, cmake and a C++ compiler (Visual Studio Build Tools with "Desktop development
with C++"). NOT TESTED by the team yet: the tested path on Windows is WSL (Ubuntu), where
dev/start_servers.sh runs as on Linux. Use WSL if this script gives you trouble.

Overrides as environment variables: LLM_PORT, EMBED_PORT, LLAMA_CPP_DIR, MODELS_DIR.
#>
param([switch]$Stop, [switch]$Status)
$ErrorActionPreference = "Stop"

$RepoDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Config = @{}
Get-Content (Join-Path $RepoDir "config.env") | ForEach-Object {
    if ($_ -match '^\s*([A-Z_0-9]+)=(.*)$') { $Config[$Matches[1]] = $Matches[2].Trim().Trim('"') }
}
function Cfg($key) { $v = [Environment]::GetEnvironmentVariable($key); if ($v) { $v } else { $Config[$key] } }
function ExpandHome($p) { $p -replace '^~', $HOME }

$LlamaDir = ExpandHome (Cfg "LLAMA_CPP_DIR")
$ModelsDir = ExpandHome (Cfg "MODELS_DIR")
$LlamaServer = Join-Path $LlamaDir "build\bin\Release\llama-server.exe"
if (-not (Test-Path $LlamaServer)) { $LlamaServer = Join-Path $LlamaDir "build\bin\llama-server.exe" }
$RunDir = Join-Path $RepoDir "dev\run"; $LogDir = Join-Path $RepoDir "dev\logs"
New-Item -ItemType Directory -Force -Path $RunDir, $LogDir, $ModelsDir | Out-Null
$LlmPort = Cfg "LLM_PORT"; $EmbedPort = Cfg "EMBED_PORT"

function Step($t) { Write-Host "`n==> $t" -ForegroundColor White }
function Ok($t) { Write-Host "  OK    $t" -ForegroundColor Green }
function Warn($t) { Write-Host "  WARN  $t" -ForegroundColor Yellow }
function Die($t) { Write-Host "`nError: $t" -ForegroundColor Red; exit 1 }
function Healthy($port) {
    try { (Invoke-RestMethod "http://127.0.0.1:$port/health" -TimeoutSec 2).status -eq "ok" } catch { $false }
}

if ($Stop) {
    Step "Stopping the servers started by this script"
    foreach ($name in "llm", "embed") {
        $pidFile = Join-Path $RunDir "$name.pid"
        if (Test-Path $pidFile) {
            $procId = Get-Content $pidFile
            try { Stop-Process -Id $procId -Force; Ok "$name (pid $procId) stopped" } catch { Warn "$name (pid $procId) was not running" }
            Remove-Item $pidFile
        }
    }
    exit 0
}
if ($Status) {
    Step "Servers"
    if (Healthy $LlmPort) { Ok "LLM answers on 127.0.0.1:$LlmPort" } else { Warn "LLM: nothing answers on port $LlmPort" }
    if (Healthy $EmbedPort) { Ok "embeddings answer on 127.0.0.1:$EmbedPort" } else { Warn "embeddings: nothing answers on port $EmbedPort" }
    exit 0
}

Step "Tools"
foreach ($tool in "git", "cmake") {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { Die "$tool is missing. Install it (winget install Git.Git / Kitware.CMake) or use WSL." }
}
Ok "git, cmake"

$Ref = Cfg "LLAMA_CPP_REF"; $Short = $Ref.Substring(0, 7)
$CpuMark = Join-Path $LlamaDir "build\.cpu-only"
$built = (Test-Path $LlamaServer) -and (Test-Path $CpuMark) -and ((& $LlamaServer --version 2>&1) -match $Short)
if ($built) {
    Ok "llama-server already built at commit $Short, CPU only"
} else {
    Step "Getting llama.cpp at commit $Short"
    if (-not (Test-Path (Join-Path $LlamaDir ".git"))) {
        git init -q $LlamaDir
        git -C $LlamaDir remote add origin (Cfg "LLAMA_CPP_REPO")
    }
    git -C $LlamaDir fetch --depth 1 origin $Ref
    git -C $LlamaDir checkout -q --detach FETCH_HEAD
    Step "Configuring: CPU only, no GPU backend"
    cmake -S $LlamaDir -B (Join-Path $LlamaDir "build") -DCMAKE_BUILD_TYPE=Release -DGGML_NATIVE=ON `
        -DGGML_CUDA=OFF -DGGML_VULKAN=OFF -DGGML_BLAS=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF
    Step "Building llama-server and llama-cli"
    cmake --build (Join-Path $LlamaDir "build") --config Release --target llama-server llama-cli
    New-Item -ItemType File -Force -Path $CpuMark | Out-Null
    $LlamaServer = Join-Path $LlamaDir "build\bin\Release\llama-server.exe"
    if (-not (Test-Path $LlamaServer)) { $LlamaServer = Join-Path $LlamaDir "build\bin\llama-server.exe" }
    Ok "built: $(& $LlamaServer --version 2>&1 | Select-String version)"
}

function Download($repo, $revision, $file, $sha) {
    Step $file
    $target = Join-Path $ModelsDir $file
    if ((Test-Path $target) -and ((Get-FileHash $target -Algorithm SHA256).Hash.ToLower() -eq $sha)) { Ok "already downloaded and verified"; return }
    $url = "https://huggingface.co/$repo/resolve/$revision/$file"
    curl.exe -L --fail --progress-bar -o "$target.part" $url
    if ((Get-FileHash "$target.part" -Algorithm SHA256).Hash.ToLower() -eq $sha) { Move-Item -Force "$target.part" $target; Ok "verified" }
    else { Remove-Item "$target.part"; Die "$file doesn't match its SHA256. Run the script again." }
}
Download (Cfg "LLM_REPO") (Cfg "LLM_REVISION") (Cfg "LLM_FILE") (Cfg "LLM_SHA256")
Download (Cfg "EMBED_REPO") (Cfg "EMBED_REVISION") (Cfg "EMBED_FILE") (Cfg "EMBED_SHA256")

# The flags below are the board's: board/systemd/math-llm.service and math-embed.service
function Launch($name, $port, $argList) {
    if (Healthy $port) { Ok "$name already answers on port $port"; return }
    $p = Start-Process -FilePath $LlamaServer -ArgumentList $argList -PassThru -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $LogDir "$name.log") -RedirectStandardError (Join-Path $LogDir "$name.err.log")
    Set-Content (Join-Path $RunDir "$name.pid") $p.Id
    for ($i = 0; $i -lt 120; $i++) { if (Healthy $port) { break }; Start-Sleep 1 }
    if (-not (Healthy $port)) { Die "$name didn't start. See $LogDir\$name.err.log" }
    Ok "$name on 127.0.0.1:$port (pid $($p.Id))"
}
Step "Starting the language model (port $LlmPort)"
Launch "llm" $LlmPort @("-m", (Join-Path $ModelsDir (Cfg "LLM_FILE")), "--host", "127.0.0.1", "--port", $LlmPort,
    "--threads", (Cfg "LLM_THREADS"), "--ctx-size", (Cfg "LLM_CTX"), "--parallel", "1", "--cache-ram", "0",
    "--ctx-checkpoints", "2", "--jinja", "--reasoning", "off", "--reasoning-budget", "0", "--alias", (Cfg "LLM_ALIAS"))
Step "Starting the embedding model (port $EmbedPort)"
Launch "embed" $EmbedPort @("-m", (Join-Path $ModelsDir (Cfg "EMBED_FILE")), "--embedding", "--host", "127.0.0.1", "--port", $EmbedPort,
    "--threads", (Cfg "EMBED_THREADS"), "--ctx-size", (Cfg "EMBED_CTX"), "--parallel", "1", "--cache-ram", "0",
    "--batch-size", (Cfg "EMBED_CTX"), "--ubatch-size", (Cfg "EMBED_CTX"))

Step "Hello world (README step 5.5)"
$body = '{"messages": [{"role": "user", "content": "Hello! What is 7 times 8? Answer in one sentence."}], "temperature": 0, "max_tokens": 40}'
$r = Invoke-RestMethod "http://127.0.0.1:$LlmPort/v1/chat/completions" -Method Post -ContentType "application/json" -Body $body
Write-Host "  answer: $($r.choices[0].message.content.Trim())"
$t = $r.timings
$est = $t.prompt_n / [double](Cfg "BOARD_PREFILL_TPS") + $t.predicted_n / [double](Cfg "BOARD_GEN_TPS")
Write-Host ("  laptop: prompt {0} tok, wrote {1} tok. Board estimate: {2:N1} s (README measured about 4 s)" -f $t.prompt_n, $t.predicted_n, $est)
Ok "Both servers run. Stop them with: dev\start_servers.ps1 -Stop"
