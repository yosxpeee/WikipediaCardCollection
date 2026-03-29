@echo off
cd /d %~dp0
if not exist .venv (
    uv init --python ">=3.11"
    uv venv
    .venv\Scripts\activate
    uv pip install BeautifulSoup4
    uv pip install requests
    uv pip install pyinstaller
    uv pip install flet==0.83.0
    uv run flet --version
    uv run flet run --hidden
) else (
    .venv\Scripts\activate
    uv run flet run --hidden
)
