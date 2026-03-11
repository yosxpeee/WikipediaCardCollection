@echo off
cd /d %~dp0
if not exist .venv (
    uv init --python='>=3.10'
    uv venv
    .venv\Scripts\activate
    uv pip install BeautifulSoup4 
    uv pip install requests
    uv add 'flet[all]'
    uv run flet --version
    uv run flet run --hidden
) else (
    .venv\Scripts\activate
    uv run flet run --hidden
)
