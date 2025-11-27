@echo off
echo Starting HoloBot GUI with DeepSeek integration...
echo.

REM Set environment variables for DeepSeek API
set DEEPSEEK_API_KEY=sk-46d540c34e57443bb668e2755d2a9dbf
set DEEPSEEK_MODEL=deepseek-chat
set DEEPSEEK_BASE_URL=https://api.deepseek.com

REM Try to run with virtual environment first, fallback to system Python
if exist ".venv\Scripts\python.exe" (
    echo Using virtual environment...
    .venv\Scripts\python.exe holobot_gui.py
) else (
    echo Using system Python...
    python holobot_gui.py
)

pause
