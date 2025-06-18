# Enable Docker BuildKit for faster, more efficient builds
$env:DOCKER_BUILDKIT = 1
$env:COMPOSE_DOCKER_CLI_BUILD = 1

Write-Host "Docker BuildKit is now enabled for faster builds" -ForegroundColor Green
Write-Host "To build the Core service with optimized settings, run:" -ForegroundColor Yellow
Write-Host "docker-compose build mcore" -ForegroundColor Cyan

# Optional: Build the Core service immediately
$buildNow = Read-Host "Do you want to build the Core service now? (y/n)"
if ($buildNow -eq "y") {
    docker-compose build mcore
}
