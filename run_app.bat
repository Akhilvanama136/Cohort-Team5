@echo off
echo =========================================================
echo   Starting Medical Pathology Assistant RAG Platform
echo =========================================================
echo.

rem Free port 8000 if a stale/hung backend is still running
echo [0/2] Checking port 8000 ...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo Stopping stale process on port 8000 (PID %%a)...
    taskkill /F /PID %%a >nul 2>&1
)
ping 127.0.0.1 -n 2 > nul

rem Start FastAPI Backend in a new window
echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "FastAPI Backend" cmd /k "title FastAPI Backend && venv\Scripts\python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 8000"

rem Wait for backend to start up (model loading can take ~15s)
echo Waiting for backend to initialize...
ping 127.0.0.1 -n 8 > nul

rem Start Streamlit Frontend
echo [2/2] Starting Streamlit Frontend ...
venv\Scripts\streamlit.exe run src/app.py --server.headless=true

echo.
echo Platform launched successfully!
echo Close the command windows to terminate the services.
echo =========================================================
