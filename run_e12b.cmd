@echo off
setlocal
rem P2_PY: the Python to use (default: python on the PATH).
cd /d "%~dp0"
if not defined P2_PY set "P2_PY=python"
set PYTHONIOENCODING=utf-8
"%P2_PY%" -X utf8 p2_e12_reaction.py rows --variant-b > logs\p2_e12b.log 2>&1
