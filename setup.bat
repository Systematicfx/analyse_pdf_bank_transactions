@echo off
echo Setting up the project...

:: Get the directory of the currently running script
set "SCRIPT_DIR=%~dp0"

:: Change to the script directory
cd /d "%SCRIPT_DIR%"

:: Check if virtualenv is installed
where virtualenv >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Installing virtualenv...
    pip install virtualenv
)

:: Create a virtual environment
echo Creating virtual environment...
virtualenv venv

:: Activate the virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

:: Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

:: Download NLTK corpora
echo Downloading NLTK corpora...
python -m nltk.downloader all

echo Setup complete! Virtual environment is ready and activated.

pause