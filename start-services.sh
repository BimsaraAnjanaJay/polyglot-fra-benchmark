#!/bin/bash
echo "🚀 Starting polyglot-fra-benchmark microservices with OpenTelemetry tracing"

# Start Docker Compose
echo "📦 Starting services..."
docker-compose -f docker-compose.otel.yml up -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 15

echo "✅ All services started!"
echo ""
echo "📊 Access Points:"
echo "  Jaeger UI: http://localhost:16686"
echo "  gateway-node: http://localhost:8080"
echo "  host-java: http://localhost:8081"
echo "  host-python: http://localhost:8082"
echo "  internal-node: http://localhost:8083"
echo "  internal-python: http://localhost:8084"
echo "  Function Analytics: http://localhost:3000/function-analytics"
