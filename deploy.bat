@echo off
REM Jarvis Production Deployment Script (Windows)
echo === Jarvis Deployment ===

echo Step 1: Running migrations...
call .venv\Scripts\python manage.py migrate --run-syncdb
if %errorlevel% neq 0 exit /b %errorlevel%

echo Step 2: Collecting static files...
call .venv\Scripts\python manage.py collectstatic --noinput
if %errorlevel% neq 0 exit /b %errorlevel%

echo Step 3: Starting services...
docker compose up -d --build web celery
if %errorlevel% neq 0 exit /b %errorlevel%

echo === Deployment complete ===
