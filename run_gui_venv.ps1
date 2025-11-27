# PowerShell script to run HoloBot GUI in virtual environment
Write-Host "Activating virtual environment and starting HoloBot GUI..." -ForegroundColor Green

# Activate virtual environment
& .\.venv\Scripts\Activate.ps1

# Set environment variables
$env:DEEPSEEK_API_KEY = "sk-46d540c34e57443bb668e2755d2a9dbf"
$env:DEEPSEEK_MODEL = "deepseek-chat"
$env:DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# Run the GUI
python holobot_gui.py

Write-Host "Press any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
