@echo off
rem NeuroFoco Studio - (re)renderiza la biblioteca de audios y la verifica.
rem Necesita Python 3.12 con numpy, scipy y lameenc (pip install numpy scipy lameenc miniaudio)
chcp 65001 >nul
cd /d "%~dp0motor"
python render_biblioteca.py
if errorlevel 1 goto fin
python verificar.py
:fin
pause
