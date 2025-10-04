# MedMatch AI Docker Setup
# Quick deployment script for healthcare AI platform

Write-Host "🏥 MedMatch AI - Docker MCP Gateway Showcase" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Check Docker installation
Write-Host "📋 Checking Docker installation..." -ForegroundColor Yellow
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker not found! Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

if (!(Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker Compose not found! Please install Docker Compose." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker installation verified" -ForegroundColor Green

# Navigate to docker directory
Set-Location $PSScriptRoot

# Check if .env file exists
if (!(Test-Path ".env")) {
    Write-Host "📝 Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "⚠️  Please edit .env file with your actual credentials:" -ForegroundColor Yellow
    Write-Host "   - SUPABASE_URL" -ForegroundColor White
    Write-Host "   - SUPABASE_ANON_KEY" -ForegroundColor White
    Write-Host "   - CEREBRAS_API_KEY" -ForegroundColor White
    Write-Host ""
    $continue = Read-Host "Continue with example values? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        Write-Host "❌ Setup cancelled. Please configure .env file first." -ForegroundColor Red
        exit 1
    }
}

# Build and start services
Write-Host "🔨 Building Docker containers..." -ForegroundColor Yellow
docker-compose build --parallel

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "🚀 Starting MedMatch AI services..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start services!" -ForegroundColor Red
    exit 1
}

# Wait for services to be ready
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service health
Write-Host "🔍 Checking service health..." -ForegroundColor Yellow
$services = @(
    @{Name="Backend API"; Url="http://localhost:8000/health"; Port=8000},
    @{Name="Frontend"; Url="http://localhost:3000"; Port=3000},
    @{Name="Prometheus"; Url="http://localhost:9090"; Port=9090},
    @{Name="Grafana"; Url="http://localhost:3001"; Port=3001}
)

foreach ($service in $services) {
    try {
        $response = Invoke-WebRequest -Uri $service.Url -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        Write-Host "✅ $($service.Name) is healthy" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️  $($service.Name) is starting... (this is normal)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "🎉 MedMatch AI Platform is starting up!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Frontend:     http://localhost:3000" -ForegroundColor White
Write-Host "Backend API:  http://localhost:8000" -ForegroundColor White
Write-Host "API Docs:     http://localhost:8000/docs" -ForegroundColor White
Write-Host "Prometheus:   http://localhost:9090" -ForegroundColor White
Write-Host "Grafana:      http://localhost:3001" -ForegroundColor White
Write-Host ""
Write-Host "📊 View logs: docker-compose logs -f" -ForegroundColor Cyan
Write-Host "🛑 Stop services: docker-compose down" -ForegroundColor Cyan
Write-Host ""
Write-Host "🏥 Ready for clinical trial matching with AI!" -ForegroundColor Magenta