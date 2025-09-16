@echo off
echo Setting up Environment Variables for AI Agent
echo ============================================

echo.
echo 1. Get your OpenWeatherMap API key from: https://openweathermap.org/api
echo 2. Get your OpenAI API key from: https://platform.openai.com/api-keys
echo.

set /p WEATHER_KEY="Enter your Weather API key (or press Enter to skip): "
set /p OPENAI_KEY="Enter your OpenAI API key (or press Enter to skip): "

if not "%WEATHER_KEY%"=="" (
    setx WEATHER_API_KEY "%WEATHER_KEY%"
    echo ✅ Weather API key set!
)

if not "%OPENAI_KEY%"=="" (
    setx OPENAI_API_KEY "%OPENAI_KEY%"
    echo ✅ OpenAI API key set!
)

echo.
echo 🔄 Please restart your terminal/IDE for changes to take effect
echo 🚀 Then run: python chat_server.py
pause

