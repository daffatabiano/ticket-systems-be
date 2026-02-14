# Development Runner Script for Windows
# Starts all backend services

Write-Host "🚀 Starting Complaint Triage System - Backend Services" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ .env file not found! Run setup.ps1 first." -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "❌ Virtual environment not found! Run setup.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "📋 Starting services..." -ForegroundColor Yellow
Write-Host ""

# Start Redis in a new window (if not already running)
Write-Host "1️⃣  Checking Redis..." -ForegroundColor Cyan
try {
    redis-cli ping | Out-Null
    Write-Host "   ✅ Redis is already running" -ForegroundColor Green
} catch {
    Write-Host "   🔄 Starting Redis in new window..." -ForegroundColor Yellow
    Start-Process -FilePath "redis-server" -WindowStyle Normal
    Start-Sleep -Seconds 2
}

# Start Celery worker in a new window
Write-Host "`n2️⃣  Starting Celery worker..." -ForegroundColor Cyan
$celeryScript = @"
Write-Host '🔧 Celery Worker' -ForegroundColor Cyan
Write-Host ''
Set-Location '$PWD'
& 'venv\Scripts\Activate.ps1'
celery -A app.workers.celery_worker worker --loglevel=info --pool=solo
"@

$celeryBlock = [ScriptBlock]::Create($celeryScript)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& {$celeryScript}" -WindowStyle Normal
Write-Host "   ✅ Celery worker started in new window" -ForegroundColor Green

# Wait a bit for worker to start
Start-Sleep -Seconds 3

# Start FastAPI in a new window
Write-Host "`n3️⃣  Starting FastAPI server..." -ForegroundColor Cyan
$fastapiScript = @"
Write-Host '🌐 FastAPI Server' -ForegroundColor Cyan
Write-Host ''
Set-Location '$PWD'
& 'venv\Scripts\Activate.ps1'
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", "& {$fastapiScript}" -WindowStyle Normal
Write-Host "   ✅ FastAPI server started in new window" -ForegroundColor Green

# Wait for server to start
Write-Host "`n⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check if API is responding
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ API is responding!" -ForegroundColor Green
    }
} catch {
    Write-Host "   ⚠️  API not responding yet (this is normal, give it a moment)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "✅ All services started!" -ForegroundColor Green
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan

Write-Host "`n📊 Service URLs:" -ForegroundColor Yellow
Write-Host "  • API Docs:    http://localhost:8000/docs" -ForegroundColor White
Write-Host "  • Health:      http://localhost:8000/health" -ForegroundColor White
Write-Host "  • WebSocket:   ws://localhost:8000/ws/tickets" -ForegroundColor White

Write-Host "`n💡 Tips:" -ForegroundColor Cyan
Write-Host "  • Watch the other PowerShell windows for logs" -ForegroundColor Gray
Write-Host "  • Press Ctrl+C in each window to stop services" -ForegroundColor Gray
Write-Host "  • API documentation: http://localhost:8000/docs" -ForegroundColor Gray

Write-Host ""
Write-Host "Press any key to exit this window..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
