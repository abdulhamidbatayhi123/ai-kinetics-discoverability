@echo off
cd /d "C:\Users\abdulhamid batayhi\Desktop\ai-kinetics-discoverability"
set PYTHONIOENCODING=utf-8
"C:\Users\abdulhamid batayhi\Desktop\ai-mof-cof-dynamics\.venv\Scripts\python.exe" -X utf8 p2_liba_fidelity.py > p2_liba.log 2>&1
echo DONE %ERRORLEVEL% >> p2_liba.log
