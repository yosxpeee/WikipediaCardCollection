@echo off
cd /d %~dp0
REM Activate virtualenv if exists, otherwise create one and install build deps
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo Virtualenv not found — creating .venv and installing build requirements
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install --upgrade pip
    pip install pyinstaller flet==0.83.0 requests beautifulsoup4 pillow
)

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "WikipediaCardCollection.spec" del /q "WikipediaCardCollection.spec"

REM Prepare icon: PyInstaller expects a .ico for Windows executables.
set ICON_PNG=src\assets\icon.png
set ICON_ICO=src\assets\icon.ico
set ICON_PNG_ABS=%CD%\%ICON_PNG%
set ICON_ICO_ABS=%CD%\%ICON_ICO%

echo Converting %ICON_PNG% -> %ICON_ICO% (requires Pillow)
python -c "from PIL import Image; img=Image.open(r'%ICON_PNG_ABS%'); img.save(r'%ICON_ICO_ABS%', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])"

REM Build single-file, windowed executable. Include assets folder so Flet can load images/SVGs.
REM Note: on Windows use a semicolon between source and destination inside the --add-data argument
set ICON_ARG=--icon "%ICON_ICO_ABS%"
pyinstaller --noconfirm --onefile --windowed %ICON_ARG% --name WikipediaCardCollection src\main.py --add-data "src\assets;assets"

if %ERRORLEVEL% equ 0 (
    echo Build finished. See dist\WikipediaCardCollection.exe
) else (
    echo Build failed with errorlevel %ERRORLEVEL%
)

pause