# Enable Docker BuildKit for faster builds
$env:DOCKER_BUILDKIT = 1
$env:COMPOSE_DOCKER_CLI_BUILD = 1

Write-Host "Rebuilding and restarting the Core service..." -ForegroundColor Green

# Stop the Core service first
docker-compose stop mcore

# Rebuild the Core service with BuildKit optimizations
Write-Host "Rebuilding Core service..." -ForegroundColor Yellow
docker-compose build mcore

# Start the Core service
Write-Host "Starting Core service..." -ForegroundColor Yellow
docker-compose up -d mcore

# Follow logs
Write-Host "Showing logs (press Ctrl+C to exit logs):" -ForegroundColor Cyan
docker-compose logs -f mcore
