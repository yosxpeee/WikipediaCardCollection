@echo off
cd /d %~dp0
if not exist .venv (
    uv init --python='>=3.10'
    uv venv
    .venv\Scripts\activate
    uv add 'flet[all]'
    uv run flet --version
    uv run flet run
) else (
    .venv\Scripts\activate
    uv run flet run
)
