#!/usr/bin/env pwsh
Write-Host "🚀 Starting polyglot-fra-benchmark microservices with OpenTelemetry tracing" -ForegroundColor Cyan

# Start Docker Compose
Write-Host "📦 Starting services..." -ForegroundColor Yellow
docker-compose -f docker-compose.otel.yml up -d

# Wait for services
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

Write-Host "\n✅ All services started!" -ForegroundColor Green
Write-Host "\n📊 Access Points:" -ForegroundColor Cyan
Write-Host "  Jaeger UI: http://localhost:16686" -ForegroundColor White
Write-Host "  gateway-node: http://localhost:8080" -ForegroundColor White
Write-Host "  host-java: http://localhost:8081" -ForegroundColor White
Write-Host "  host-python: http://localhost:8082" -ForegroundColor White
Write-Host "  internal-node: http://localhost:8083" -ForegroundColor White
Write-Host "  internal-python: http://localhost:8084" -ForegroundColor White
Write-Host "  Function Analytics: http://localhost:3000/function-analytics" -ForegroundColor White
