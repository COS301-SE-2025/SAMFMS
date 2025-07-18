#!/usr/bin/env python3
"""
Test runner script for SAMFMS integration tests
"""

import sys
import os
import subprocess
import argparse
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_command(command, cwd=None, env=None):
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {command}")
        return None
    except Exception as e:
        logger.error(f"Error running command: {command}, Error: {e}")
        return None


def setup_test_environment():
    """Set up test environment"""
    logger.info("Setting up test environment...")
    
    # Create test logs directory
    logs_dir = project_root / "tests" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test coverage directory
    coverage_dir = project_root / "tests" / "coverage"
    coverage_dir.mkdir(parents=True, exist_ok=True)
    
    # Install test dependencies
    logger.info("Installing test dependencies...")
    result = run_command("pip install -r tests/requirements.txt", cwd=project_root)
    if result and result.returncode != 0:
        logger.error("Failed to install test dependencies")
        return False
    
    logger.info("Test environment setup complete")
    return True


def run_unit_tests():
    """Run unit tests"""
    logger.info("Running unit tests...")
    
    command = "pytest tests/unit -v --tb=short --cov=Core --cov=Sblocks --cov-report=term-missing"
    result = run_command(command, cwd=project_root)
    
    if result:
        logger.info(f"Unit tests completed with return code: {result.returncode}")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode == 0
    
    return False


def run_integration_tests():
    """Run integration tests"""
    logger.info("Running integration tests...")
    
    command = "pytest tests/integration -v --tb=short --cov=Core --cov=Sblocks --cov-report=html:tests/coverage/html"
    result = run_command(command, cwd=project_root)
    
    if result:
        logger.info(f"Integration tests completed with return code: {result.returncode}")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode == 0
    
    return False


def run_service_tests():
    """Run service-specific tests"""
    logger.info("Running service tests...")
    
    # Test Core service
    logger.info("Testing Core service...")
    command = "pytest tests/integration/test_core_routes_integration.py -v"
    result = run_command(command, cwd=project_root)
    
    if not result or result.returncode != 0:
        logger.error("Core service tests failed")
        return False
    
    # Test service integration
    logger.info("Testing service integration...")
    command = "pytest tests/integration/test_service_integration.py -v"
    result = run_command(command, cwd=project_root)
    
    if not result or result.returncode != 0:
        logger.error("Service integration tests failed")
        return False
    
    logger.info("Service tests completed successfully")
    return True


def run_all_tests():
    """Run all tests"""
    logger.info("Running all tests...")
    
    command = "pytest tests/ -v --tb=short --cov=Core --cov=Sblocks --cov-report=html:tests/coverage/html --cov-report=xml:tests/coverage/coverage.xml"
    result = run_command(command, cwd=project_root)
    
    if result:
        logger.info(f"All tests completed with return code: {result.returncode}")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode == 0
    
    return False


def check_docker_services():
    """Check if Docker services are running"""
    logger.info("Checking Docker services...")
    
    # Check if Docker is running
    result = run_command("docker ps")
    if not result or result.returncode != 0:
        logger.error("Docker is not running or not accessible")
        return False
    
    # Check if SAMFMS services are running
    result = run_command("docker-compose -f docker-compose.test.yml ps")
    if not result or result.returncode != 0:
        logger.warning("SAMFMS test services are not running")
        return False
    
    logger.info("Docker services are running")
    return True


def start_test_services():
    """Start test services"""
    logger.info("Starting test services...")
    
    # Stop existing services
    run_command("docker-compose -f docker-compose.test.yml down", cwd=project_root)
    
    # Start test services
    result = run_command("docker-compose -f docker-compose.test.yml up -d", cwd=project_root)
    if not result or result.returncode != 0:
        logger.error("Failed to start test services")
        return False
    
    # Wait for services to be ready
    import time
    logger.info("Waiting for services to be ready...")
    time.sleep(30)
    
    return True


def stop_test_services():
    """Stop test services"""
    logger.info("Stopping test services...")
    
    result = run_command("docker-compose -f docker-compose.test.yml down", cwd=project_root)
    if not result or result.returncode != 0:
        logger.warning("Failed to stop test services")
        return False
    
    return True


def generate_test_report():
    """Generate test report"""
    logger.info("Generating test report...")
    
    # Generate coverage report
    command = "coverage html -d tests/coverage/html"
    result = run_command(command, cwd=project_root)
    
    if result and result.returncode == 0:
        logger.info("Test coverage report generated: tests/coverage/html/index.html")
    
    # Generate XML report for CI
    command = "coverage xml -o tests/coverage/coverage.xml"
    result = run_command(command, cwd=project_root)
    
    if result and result.returncode == 0:
        logger.info("Test coverage XML report generated: tests/coverage/coverage.xml")
    
    return True


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="SAMFMS Test Runner")
    parser.add_argument("--test-type", choices=["unit", "integration", "service", "all"], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--setup", action="store_true", help="Set up test environment")
    parser.add_argument("--start-services", action="store_true", help="Start test services")
    parser.add_argument("--stop-services", action="store_true", help="Stop test services")
    parser.add_argument("--report", action="store_true", help="Generate test report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    success = True
    
    try:
        if args.setup:
            success &= setup_test_environment()
        
        if args.start_services:
            success &= start_test_services()
        
        if args.test_type == "unit":
            success &= run_unit_tests()
        elif args.test_type == "integration":
            success &= run_integration_tests()
        elif args.test_type == "service":
            success &= run_service_tests()
        elif args.test_type == "all":
            success &= run_all_tests()
        
        if args.report:
            generate_test_report()
        
        if args.stop_services:
            stop_test_services()
        
    except KeyboardInterrupt:
        logger.info("Test run interrupted by user")
        success = False
    except Exception as e:
        logger.error(f"Test run failed: {e}")
        success = False
    
    if success:
        logger.info("All tests completed successfully")
        sys.exit(0)
    else:
        logger.error("Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
