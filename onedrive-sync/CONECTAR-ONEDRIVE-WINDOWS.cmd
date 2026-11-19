@echo off
setlocal EnableExtensions
title Mi Control de Alicuotas - Conectar OneDrive personal
if not exist "%~dp0vincular-onedrive.ps1" (
    echo No se encontro el asistente. Extrae primero la carpeta completa del ZIP.
    pause
    exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0vincular-onedrive.ps1"
echo.
echo Presiona cualquier tecla para cerrar la ventana.
pause >nul
