# Backend - Sistem Triage Keluhan

Backend API menggunakan FastAPI dengan Celery untuk background processing.

## Setup

```powershell
# Install dependencies
pip install -r requirements.txt

# Copy dan edit .env
copy .env.example .env
notepad .env
```

## Jalankan

**Development mode:**
```powershell
# Start backend API
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start Celery worker (di terminal terpisah)
python -m celery -A app.workers.celery_worker:celery_app worker --loglevel=info --pool=solo
```

## Konfigurasi Penting

Edit file `.env`:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/complaint_triage

# Redis
REDIS_URL=redis://localhost:6379/0

# AI (wajib untuk processing)
ANTHROPIC_API_KEY=your-api-key-here

# CORS (sesuaikan dengan frontend URL)
CORS_ORIGINS=["http://localhost:3000"]
```

## API Endpoints

- `POST /api/tickets/` - Buat tiket baru
- `GET /api/tickets/` - List semua tiket
- `GET /api/tickets/{id}` - Detail tiket
- `PATCH /api/tickets/{id}` - Update tiket
- `POST /api/tickets/{id}/resolve` - Resolve tiket
- `GET /health` - Health check

Dokumentasi lengkap: http://localhost:8000/docs

## Testing

```powershell
# Run tests
pytest tests/ -v

# Dengan coverage
pytest tests/ --cov=app
```

## Troubleshooting

**Database error:**
```powershell
# Pastikan PostgreSQL jalan
Get-Service postgresql*

# Buat database kalau belum ada
psql -U postgres -c "CREATE DATABASE complaint_triage;"
```

**Redis error:**
```powershell
# Pastikan Redis jalan
Get-Process redis-server

# Start Redis kalau belum jalan
redis-server
```

**Celery worker tidak start:**
- Pastikan ANTHROPIC_API_KEY sudah diset di .env
- Pastikan Redis jalan
- Restart dengan `--pool=solo` untuk Windows
