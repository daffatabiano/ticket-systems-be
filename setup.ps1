# Backend Setup Script for Windows
# Run this script in PowerShell

Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "🚀 Setting up Complaint Triage System - Backend" -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan

# Check Python installation
Write-Host "`n📋 Checking prerequisites..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found! Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check PostgreSQL
try {
    $pgVersion = psql --version 2>&1
    Write-Host "✅ PostgreSQL found: $pgVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠️  PostgreSQL not found in PATH. Make sure it's installed." -ForegroundColor Yellow
}

# Check Redis
try {
    $redisVersion = redis-server --version 2>&1
    Write-Host "✅ Redis found" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Redis not found. You'll need to install it or use Docker." -ForegroundColor Yellow
}

# Create virtual environment
Write-Host "`n🐍 Creating virtual environment..." -ForegroundColor Yellow

if (Test-Path "venv") {
    Write-Host "ℹ️  Virtual environment already exists" -ForegroundColor Cyan
} else {
    python -m venv venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "`n🔧 Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "`n📦 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Create .env file
Write-Host "`n📝 Setting up environment configuration..." -ForegroundColor Yellow

if (Test-Path ".env") {
    Write-Host "ℹ️  .env file already exists" -ForegroundColor Cyan
} else {
    Copy-Item ".env.example" ".env"
    Write-Host "✅ .env file created from .env.example" -ForegroundColor Green
    Write-Host "⚠️  IMPORTANT: Edit .env and set your ANTHROPIC_API_KEY!" -ForegroundColor Yellow
}

# Initialize database
Write-Host "`n🗄️  Database setup..." -ForegroundColor Yellow
Write-Host "To initialize the database, run:" -ForegroundColor Cyan
Write-Host "  python scripts\init_db.py" -ForegroundColor White

Write-Host "`n" -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "✅ Backend setup complete!" -ForegroundColor Green
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan

Write-Host "`n📋 Next steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Edit .env file and set your ANTHROPIC_API_KEY" -ForegroundColor White
Write-Host "   ANTHROPIC_API_KEY=sk-ant-api03-your-key-here" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Make sure PostgreSQL is running" -ForegroundColor White
Write-Host ""
Write-Host "3. Initialize the database:" -ForegroundColor White
Write-Host "   python scripts\init_db.py" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Start Redis (in a separate terminal):" -ForegroundColor White
Write-Host "   redis-server" -ForegroundColor Gray
Write-Host "   # OR use Docker: docker run -d -p 6379:6379 redis:7-alpine" -ForegroundColor Gray
Write-Host ""
Write-Host "5. Start Celery worker (in a separate terminal):" -ForegroundColor White
Write-Host "   celery -A app.workers.celery_worker worker --loglevel=info --pool=solo" -ForegroundColor Gray
Write-Host ""
Write-Host "6. Start FastAPI server:" -ForegroundColor White
Write-Host "   uvicorn app.main:app --reload" -ForegroundColor Gray
Write-Host ""
Write-Host "7. Open API docs in browser:" -ForegroundColor White
Write-Host "   http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "💡 Tip: Use 'run_dev.ps1' script to start all services in one command" -ForegroundColor Cyan
Write-Host ""
