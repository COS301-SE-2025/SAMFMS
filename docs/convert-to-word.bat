@echo off
echo Converting Markdown to Word...
echo =============================

REM Check if Pandoc is installed
pandoc --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Pandoc is not installed!
    echo.
    echo Please install Pandoc using one of these methods:
    echo 1. winget install JohnMacFarlane.Pandoc
    echo 2. Download from: https://pandoc.org/installing.html
    echo.
    echo Alternative: Use online converter at https://pandoc.org/try/
    pause
    exit /b 1
)

REM Convert the technical guide
echo Converting Technical_Installation_Guide.md to Word format...
pandoc Technical_Installation_Guide.md -o Technical_Installation_Guide.docx --toc --number-sections --highlight-style=github

if %errorlevel% equ 0 (
    echo.
    echo ✅ Success! Created Technical_Installation_Guide.docx
    echo.
    echo Opening the Word document...
    start "" "Technical_Installation_Guide.docx"
) else (
    echo ❌ Error: Conversion failed
)

echo.
pause
