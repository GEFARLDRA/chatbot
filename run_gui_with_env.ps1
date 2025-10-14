# PowerShell script to run HoloBot GUI with environment variables
Write-Host "Setting up environment and starting HoloBot GUI..." -ForegroundColor Green

# Set environment variables
$env:DEEPSEEK_API_KEY = "sk-1160f813950f4cee927f102ce16d145d"
$env:DEEPSEEK_MODEL = "deepseek-chat"
$env:DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# Run the GUI
python holobot_gui.py

Write-Host "Press any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
