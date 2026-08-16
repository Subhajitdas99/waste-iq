@echo off
setlocal
rem Windows launcher for the wiq CLI (works from PowerShell and cmd.exe).
set "WIQ_DIR=%~dp0"
pushd "%WIQ_DIR%"
if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)
"%PYTHON%" -m cli %*
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%
