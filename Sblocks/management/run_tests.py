#!/usr/bin/env python3
"""
Test runner script for the management sblock
Provides convenient commands to run different test suites
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle output"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode != 0:
            print(f"❌ Command failed with return code {result.returncode}")
            return False
        else:
            print("✅ Command completed successfully")
            return True
            
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test runner for management sblock")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--vehicle", action="store_true", help="Run vehicle-related tests only")
    parser.add_argument("--coverage", action="store_true", help="Run tests with coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--file", help="Run specific test file")
    parser.add_argument("--test", help="Run specific test function")
    parser.add_argument("--markers", action="store_true", help="List available test markers")
    
    args = parser.parse_args()
    
    # Base pytest command
    base_cmd = ["python", "-m", "pytest"]
    
    if args.markers:
        run_command(base_cmd + ["--markers"], "Listing available test markers")
        return
    
    # Build command based on arguments
    if args.verbose:
        base_cmd.append("-v")
    
    if args.coverage:
        base_cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term", "--cov-report=xml"])
    
    # Determine what to run
    if args.file:
        # Run specific file
        test_target = f"tests/{args.file}" if not args.file.startswith("tests/") else args.file
        if args.test:
            test_target += f"::{args.test}"
        cmd = base_cmd + [test_target]
        run_command(cmd, f"Running specific test: {test_target}")
        
    elif args.unit and args.integration:
        # Run both unit and integration tests
        print("Running both unit and integration tests...")
        success = True
        success &= run_command(base_cmd + ["-m", "unit"], "Unit tests")
        success &= run_command(base_cmd + ["-m", "integration"], "Integration tests")
        if not success:
            sys.exit(1)
            
    elif args.unit:
        # Run unit tests, optionally filtered by vehicle marker
        cmd = base_cmd.copy()
        if args.vehicle:
            cmd.extend(["-m", "unit and vehicle"])
        else:
            cmd.extend(["-m", "unit"])
        run_command(cmd, "Unit tests")
        
    elif args.integration:
        # Run integration tests, optionally filtered by vehicle marker
        cmd = base_cmd.copy()
        if args.vehicle:
            cmd.extend(["-m", "integration and vehicle"])
        else:
            cmd.extend(["-m", "integration"])
        run_command(cmd, "Integration tests")
        
    elif args.vehicle:
        # Run vehicle tests only
        cmd = base_cmd + ["-m", "vehicle"]
        run_command(cmd, "Vehicle-related tests")
        
    else:
        # Run all tests
        print("Running all tests...")
        success = True
        
        # Run unit tests
        success &= run_command(base_cmd + ["-m", "unit"], "Unit tests")
        
        # Run integration tests
        success &= run_command(base_cmd + ["-m", "integration"], "Integration tests")
        
        if not success:
            print("\n❌ Some tests failed!")
            sys.exit(1)
        else:
            print("\n✅ All tests passed!")
    
    print(f"\n{'='*60}")
    print("Test run completed!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
