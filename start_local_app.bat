@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Python virtual environment was not found.
  echo Please keep this window open and ask Codex to rebuild .venv.
  pause
  exit /b 1
)

echo Starting AI Resume Screening Copilot...
echo Keep the server window open while using the webpage.

powershell.exe -NoProfile -Command "try { $r=Invoke-WebRequest -Uri 'http://localhost:8502/_stcore/health' -UseBasicParsing -TimeoutSec 1; if ($r.StatusCode -eq 200) { exit 0 } } catch {}; exit 1"
if not errorlevel 1 (
  echo The local service is already running.
  start "" "http://localhost:8502"
  exit /b 0
)

start "Resume Copilot Server" cmd /k "cd /d ""%~dp0"" && .venv\Scripts\python.exe -m streamlit run app.py --server.port=8502"

powershell.exe -NoProfile -Command "$ok=$false; 1..20 | ForEach-Object { try { $r=Invoke-WebRequest -Uri 'http://localhost:8502/_stcore/health' -UseBasicParsing -TimeoutSec 1; if ($r.StatusCode -eq 200) { $ok=$true; break } } catch {}; Start-Sleep -Milliseconds 500 }; if (-not $ok) { exit 1 }"
if errorlevel 1 (
  echo [ERROR] The local service did not start. Check the Resume Copilot Server window.
  pause
  exit /b 1
)

start "" "http://localhost:8502"
exit /b 0
