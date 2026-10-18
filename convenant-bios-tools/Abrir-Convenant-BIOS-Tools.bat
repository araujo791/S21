@echo off
setlocal
cd /d "%~dp0"
if exist "runtime\windows\python.exe" (
  "runtime\windows\python.exe" -E -s "convenant_bios_tools.py"
) else (
  echo Runtime portatil ausente. Extraia o pacote completo antes de abrir.
  echo Para desenvolvimento com Python instalado: python convenant_bios_tools.py
)
pause
