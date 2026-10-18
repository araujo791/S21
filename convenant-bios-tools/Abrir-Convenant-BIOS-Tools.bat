@echo off
cd /d "%~dp0"
if exist "Convenant-BIOS-Tools.exe" (
  start "" "%~dp0Convenant-BIOS-Tools.exe"
) else (
  echo Baixe e extraia o pacote nativo 0.2.0 para abrir o executavel.
  pause
)
