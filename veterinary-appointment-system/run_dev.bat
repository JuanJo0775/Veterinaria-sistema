cd@echo off
REM run_dev.bat - Batch file para Windows
echo === Starting Veterinary System Development Server ===

REM Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python no está instalado o no está en el PATH
    pause
    exit /b 1
)

REM Instalar dependencias si es necesario
echo Verificando dependencias...
pip install psutil flask flask-cors requests python-dotenv flask-sqlalchemy flask-jwt-extended flask-mail marshmallow bcrypt psycopg2-binary

REM Ejecutar el script principal
python run_services.py

pause