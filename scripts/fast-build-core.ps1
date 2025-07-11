# Fast build script for Core service with optimization (PowerShell)

Write-Host "🚀 Starting optimized Core service build..." -ForegroundColor Green

# Enable BuildKit for better caching and parallelization
$env:DOCKER_BUILDKIT = "1"
$env:COMPOSE_DOCKER_CLI_BUILD = "1"

try {
    # Build only Core service (fastest approach)
    Write-Host "Building Core service only..." -ForegroundColor Yellow
    docker-compose build core
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Core service build completed successfully!" -ForegroundColor Green
        
        # Optional: Clean up dangling images to save space
        Write-Host "🧹 Cleaning up dangling images..." -ForegroundColor Yellow
        docker image prune -f
        
        Write-Host "🎉 Build optimization complete!" -ForegroundColor Green
    } else {
        Write-Host "❌ Build failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
} catch {
    Write-Host "❌ Build failed with error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
