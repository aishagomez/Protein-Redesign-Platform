@echo off
REM ─────────────────────────────────────────────────────────────
REM  build.bat  —  Construye bio-cli.exe con PyInstaller
REM  Requisitos: Python 3.10+, pip
REM ─────────────────────────────────────────────────────────────

echo [1/4] Creando entorno virtual...
python -m venv .venv
call .venv\Scripts\activate.bat

echo [2/4] Instalando dependencias...
pip install --upgrade pip --quiet
pip install typer[all] httpx rich pyinstaller --quiet

echo [3/4] Compilando ejecutable...
pyinstaller cli.spec --clean --noconfirm

echo [4/4] Listo!
echo.
echo  El ejecutable esta en:  dist\bio-cli.exe
echo.
echo  Pruebalo con:
echo    dist\bio-cli.exe --help
echo    dist\bio-cli.exe auth login
echo    dist\bio-cli.exe projects list
echo.
pause
