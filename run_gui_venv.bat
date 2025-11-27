@echo off
echo Activating virtual environment and starting HoloBot GUI...
call .venv\Scripts\activate.bat
set DEEPSEEK_API_KEY=sk-46d540c34e57443bb668e2755d2a9dbf
set DEEPSEEK_MODEL=deepseek-chat
set DEEPSEEK_BASE_URL=https://api.deepseek.com
python holobot_gui.py
pause
