@echo off
title ESP32 Encoder Viewer
echo Verificando dependencias...

python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado. Instale em https://python.org
    pause
    exit /b 1
)

python -c "import serial" >nul 2>&1
if errorlevel 1 (
    echo Instalando pyserial...
    pip install pyserial
)

echo Iniciando visualizador...
python viewer.py
