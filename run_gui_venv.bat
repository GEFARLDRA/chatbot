@echo off
echo Activating virtual environment and starting HoloBot GUI...
call .venv\Scripts\activate.bat
set DEEPSEEK_API_KEY=sk-1160f813950f4cee927f102ce16d145d
set DEEPSEEK_MODEL=deepseek-chat
set DEEPSEEK_BASE_URL=https://api.deepseek.com
python holobot_gui.py
pause
