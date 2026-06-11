@echo off
cd /d "C:\Users\User\Downloads\-UI-selenium-Automation"
call "C:\Users\User\Downloads\-UI-selenium-Automation\venv\Scripts\activate.bat"
python "C:\Users\User\Downloads\-UI-selenium-Automation\testes.py" --all --headless
exit /b %ERRORLEVEL%
