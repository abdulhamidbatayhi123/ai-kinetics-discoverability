@echo off
setlocal
rem P2_PY: the Python to use (default: python on the PATH).
cd /d "%~dp0.."
if not defined P2_PY set "P2_PY=python"
set PYTHONIOENCODING=utf-8
"%P2_PY%" -X utf8 kaggle_e11\queue.py >> kaggle_e11\queue.log 2>&1
