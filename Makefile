# SAMFMS Test Suite Makefile

.PHONY: help test test-security test-core test-unit test-integration test-coverage clean

help: ## Show this help message
	@echo "SAMFMS Test Suite Commands"
	@echo "=========================="
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

test: ## Run all tests for all services
	@echo "🧪 Running all tests..."
	@.\run-tests.bat

test-security: ## Run all security service tests
	@echo "🔐 Running security tests..."
	@.\run-tests.bat --service security

test-core: ## Run all core service tests
	@echo "⚙️ Running core tests..."
	@.\run-tests.bat --service core

test-unit: ## Run unit tests only
	@echo "🔬 Running unit tests..."
	@.\run-tests.bat --unit

test-integration: ## Run integration tests only
	@echo "🔗 Running integration tests..."
	@.\run-tests.bat --integration

test-coverage: ## Run tests with coverage reports
	@echo "📊 Running tests with coverage..."
	@.\run-tests.bat --coverage

test-security-unit: ## Run security unit tests only
	@echo "🔐🔬 Running security unit tests..."
	@.\run-tests.bat --service security --unit

test-security-integration: ## Run security integration tests only
	@echo "🔐🔗 Running security integration tests..."
	@.\run-tests.bat --service security --integration

clean: ## Clean up test containers and reports
	@echo "🧹 Cleaning up..."
	@docker-compose -f docker-compose.test.yml down --volumes --remove-orphans
	@if exist "Sblocks\security\test-reports" rmdir /s /q "Sblocks\security\test-reports"
	@echo "Clean up complete!"

build-test: ## Build test environment
	@echo "🏗️ Building test environment..."
	@docker-compose -f docker-compose.test.yml build

# Quick aliases
security: test-security ## Alias for test-security
core: test-core ## Alias for test-core
unit: test-unit ## Alias for test-unit
integration: test-integration ## Alias for test-integration
coverage: test-coverage ## Alias for test-coverage
