@echo off
title Real Estate Project — Launcher
color 0A
cls

echo.
echo  ============================================================
echo   🏡  REAL ESTATE WEBSITE — PROJECT LAUNCHER
echo  ============================================================
echo.

:: ── Resolve project root (folder containing this script) ─────────────────────
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

set "AI_DIR=%ROOT%\ai_service"
set "BACKEND_DIR=%ROOT%\backend\WebApiShop"
set "FRONTEND_DIR=%ROOT%\frontend"

:: ── 1. Check prerequisites ────────────────────────────────────────────────────
echo  [1/4] Checking prerequisites...
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found. Install Python 3.11+ and add it to PATH.
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo         ✔  %%v

where dotnet >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] .NET SDK not found. Install .NET 8 SDK.
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('dotnet --version 2^>^&1') do echo         ✔  .NET %%v

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Node.js not found. Install Node.js 20+.
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('node --version 2^>^&1') do echo         ✔  Node.js %%v

where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] npm not found.
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('npm --version 2^>^&1') do echo         ✔  npm %%v

echo.

:: ── 2. Check .env file ────────────────────────────────────────────────────────
echo  [2/4] Checking configuration...
echo.

if not exist "%AI_DIR%\.env" (
    echo  [ERROR] Missing ai_service\.env file.
    echo          Create it with:
    echo          OPENAI_API_KEY=sk-your-key-here
    echo          STORE_NAME=Your Store Name
    echo          STORE_DESCRIPTION=Your description here.
    pause & exit /b 1
)
echo         ✔  ai_service\.env found

:: Check OPENAI_API_KEY is not placeholder
findstr /i "sk-your-key" "%AI_DIR%\.env" >nul 2>&1
if %errorlevel% equ 0 (
    echo  [WARNING] OPENAI_API_KEY looks like a placeholder. Update it in ai_service\.env
)

echo.

:: ── 3. Install Python dependencies ───────────────────────────────────────────
echo  [3/4] Installing Python dependencies...
echo.

pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo         Installing: fastapi uvicorn openai python-dotenv python-multipart
    pip install fastapi uvicorn openai python-dotenv python-multipart --quiet
    if %errorlevel% neq 0 (
        echo  [ERROR] pip install failed.
        pause & exit /b 1
    )
) else (
    echo         ✔  Python packages already installed
)

:: python-multipart is required for FastAPI UploadFile — install separately if missing
pip show python-multipart >nul 2>&1
if %errorlevel% neq 0 (
    echo         Installing: python-multipart
    pip install python-multipart --quiet
)

echo.

:: ── 4. Install Node dependencies ─────────────────────────────────────────────
echo  [4/4] Checking Node dependencies...
echo.

if not exist "%FRONTEND_DIR%\node_modules" (
    echo         Running npm install — this may take a minute...
    pushd "%FRONTEND_DIR%"
    call npm install --silent
    if %errorlevel% neq 0 (
        echo  [ERROR] npm install failed.
        popd & pause & exit /b 1
    )
    popd
) else (
    echo         ✔  node_modules already present
)

echo.
echo  ============================================================
echo   Starting all 3 services...
echo  ============================================================
echo.

:: ── Start Python AI Service (port 8001) ──────────────────────────────────────
echo  🐍  Starting Python AI Service on http://localhost:8001 ...
start "🐍 AI Service — port 8001" cmd /k "color 0B && title AI Service ^(Python^) && cd /d "%AI_DIR%" && echo. && echo  AI Service starting... && echo  Swagger UI: http://localhost:8001/docs && echo. && uvicorn chat_service:app --port 8001 --reload"

:: Give Python a moment to bind the port
timeout /t 3 /nobreak >nul

:: ── Start .NET Backend (IIS Express port 44305) ───────────────────────────────
echo  ⚙️   Starting .NET Backend on https://localhost:44305 ...
start "⚙️ Backend — .NET 8 (port 44305)" cmd /k "color 0E && title Backend ^(.NET 8^) && cd /d "%BACKEND_DIR%" && echo. && echo  Backend starting... && echo  Swagger UI: https://localhost:44305/swagger && echo. && dotnet run --launch-profile IIS Express"

:: Give .NET a moment to compile and start
timeout /t 5 /nobreak >nul

:: ── Start Angular Frontend (port 4200) ───────────────────────────────────────
echo  🅰️   Starting Angular Frontend on http://localhost:4200 ...
start "🅰️ Frontend — Angular (port 4200)" cmd /k "color 0D && title Frontend ^(Angular^) && cd /d "%FRONTEND_DIR%" && echo. && echo  Angular starting... && echo  App: http://localhost:4200 && echo. && npm start"

:: ── Done ─────────────────────────────────────────────────────────────────────
echo.
echo  ============================================================
echo   ✅  All 3 services launched in separate windows!
echo  ============================================================
echo.
echo   Service          URL
echo   ───────────────  ──────────────────────────────────────
echo   Angular App      http://localhost:4200
echo   .NET API         https://localhost:44305/swagger
echo   Python AI        http://localhost:8001/docs
echo  ============================================================
echo.
echo   Press any key to open the app in your browser...
pause >nul

start "" "http://localhost:4200"
exit
