#!/bin/bash
# Fast build script for Core service with optimization

echo "🚀 Starting optimized Core service build..."

# Build with BuildKit for better caching and parallelization
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Option 1: Build only Core service (fastest)
echo "Building Core service only..."
docker-compose build core

# Option 2: Build with cache mount (even faster on subsequent builds)
# Uncomment below if you want to use cache mounts
# docker build \
#   --build-arg BUILDKIT_INLINE_CACHE=1 \
#   --cache-from core:latest \
#   -t core:latest \
#   -f Core/Dockerfile .

echo "✅ Core service build completed!"

# Optional: Remove dangling images to save space
echo "🧹 Cleaning up dangling images..."
docker image prune -f

echo "🎉 Build optimization complete!"
