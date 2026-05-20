@echo off
setlocal

set "ROOT=%~dp0"
set "PYTHON=%ROOT%.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo [ERROR] Virtual environment was not found at "%PYTHON%".
    echo Create it first with: py -3.12 -m venv .venv
    echo Then install dependencies with: .venv\Scripts\python.exe -m pip install -r requirements.txt
    exit /b 1
)

pushd "%ROOT%"
"%PYTHON%" -m streamlit run "app/ui.py" %*
set "EXIT_CODE=%ERRORLEVEL%"
popd

exit /b %EXIT_CODE%