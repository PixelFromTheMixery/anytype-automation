@echo off
REM Setting directory to script
cd /d %~dp0


REM Get current date and set variables
for /f "tokens=2-4 delims=/.- " %%a in ('date /t') do (
    set year=%%c
    set month=%%b
    set day=%%a
)

REM Check Month Directory
if not exist logs\%year%\%month%\ mkdir logs\%year%\%month%

REM Set log path
set log_path=.\logs\%year%\%month%\%day%.log
echo Currently in %cd% >> %log_path%

echo [%date% %time%] Starting script >> %log_path%

REM Run the Python script and redirect output to console
.venv\Scripts\python "main.py" --m --c >> %log_path% 2>&1

echo [%date% %time%] Script finished >>  %log_path%

echo [%date% %time%] Closing >>  %log_path%
exit /b

echo [%date% %time%] Should have closed >>  %log_path%