@echo off
echo Starting Game Trading Platform server...
echo ======================================

REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo Virtual environment not found, trying to run with system Python...
)

REM Check if requirements are installed
echo Checking dependencies...
pip install -r requirements.txt

REM Initialize database if needed
echo Setting up database and static files...
python main.py --init

REM Start the server
echo Starting server...
python main.py

echo Server is stopped
pause 