#!/usr/bin/env python3
"""
Maintenance Service Configuration Fix Script
Fixes common configuration issues and validates setup
"""

import os
import json
import socket
import subprocess
from pathlib import Path

class MaintenanceServiceFixer:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.fixes_applied = []
        
    def fix_environment_variables(self):
        """Fix environment variable inconsistencies"""
        env_file = self.base_path / ".env"
        
        if not env_file.exists():
            print("❌ .env file not found")
            return
            
        with open(env_file, 'r') as f:
            content = f.read()
            
        fixes = []
        
        # Fix maintenance port variable naming
        if "MAINTENANCE_SERVICE_PORT=21007" in content and "MAINTENANCE_PORT" not in content:
            content += "\nMAINTENANCE_PORT=21007\n"
            fixes.append("Added MAINTENANCE_PORT for backward compatibility")
            
        # Fix database name consistency
        if "DATABASE_MAINTENANCE=samfms_maintenance" not in content:
            content += "\nDATABASE_MAINTENANCE=samfms_maintenance\n"
            fixes.append("Added DATABASE_MAINTENANCE variable")
            
        # Fix RabbitMQ URL encoding
        if "RabbitPass2025%21" in content:
            content = content.replace("RabbitPass2025%21", "RabbitPass2025!")
            fixes.append("Fixed RabbitMQ URL encoding")
            
        if fixes:
            with open(env_file, 'w') as f:
                f.write(content)
            self.fixes_applied.extend(fixes)
            print("✅ Environment variables fixed")
        else:
            print("✅ Environment variables are correct")
            
    def fix_main_py_configuration(self):
        """Fix main.py configuration issues"""
        main_file = self.base_path / "Sblocks" / "maintenance" / "main.py"
        
        if not main_file.exists():
            print("❌ main.py not found")
            return
            
        with open(main_file, 'r') as f:
            content = f.read()
            
        fixes = []
        
        # Fix port environment variable
        if 'os.getenv("MAINTENANCE_PORT"' in content:
            content = content.replace(
                'os.getenv("MAINTENANCE_PORT", "8000")',
                'os.getenv("MAINTENANCE_SERVICE_PORT", "21007")'
            )
            fixes.append("Fixed port environment variable")
            
        # Fix database name
        if 'os.getenv("DATABASE_NAME"' in content:
            content = content.replace(
                'os.getenv("DATABASE_NAME", "samfms_maintenance")',
                'os.getenv("DATABASE_MAINTENANCE", "samfms_maintenance")'
            )
            fixes.append("Fixed database name environment variable")
            
        if fixes:
            with open(main_file, 'w') as f:
                f.write(content)
            self.fixes_applied.extend(fixes)
            print("✅ main.py configuration fixed")
        else:
            print("✅ main.py configuration is correct")
            
    def create_missing_directories(self):
        """Create missing directories for proper service structure"""
        directories = [
            "Sblocks/maintenance/uploads/maintenance",
            "Sblocks/maintenance/uploads/licenses",
            "Sblocks/maintenance/logs",
            "Sblocks/maintenance/temp"
        ]
        
        for dir_path in directories:
            full_path = self.base_path / dir_path
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                self.fixes_applied.append(f"Created directory: {dir_path}")
                
        print("✅ Directory structure verified")
        
    def validate_docker_configuration(self):
        """Validate Docker configuration"""
        docker_compose = self.base_path / "docker-compose.yml"
        
        if not docker_compose.exists():
            print("⚠️ docker-compose.yml not found")
            return
            
        with open(docker_compose, 'r') as f:
            content = f.read()
            
        issues = []
        
        # Check if maintenance service is defined
        if "maintenance:" not in content:
            issues.append("Maintenance service not defined in docker-compose.yml")
            
        # Check port mapping
        if "21007:8000" not in content and "21007:21007" not in content:
            issues.append("Maintenance service port mapping not configured")
            
        if issues:
            print("⚠️ Docker configuration issues found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✅ Docker configuration looks good")
            
    def validate_service_connectivity(self):
        """Validate service connectivity"""
        services = {
            "MongoDB": ("localhost", 21003),
            "RabbitMQ": ("localhost", 21000),
            "RabbitMQ Management": ("localhost", 21001),
            "Core Service": ("localhost", 21004)
        }
        
        for service_name, (host, port) in services.items():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    print(f"✅ {service_name} is accessible on {host}:{port}")
                else:
                    print(f"❌ {service_name} is not accessible on {host}:{port}")
            except Exception as e:
                print(f"❌ {service_name} connectivity check failed: {e}")
                    
    def generate_startup_script(self):
        """Generate maintenance service startup script"""
        script_content = """#!/bin/bash
# Maintenance Service Startup Script

echo "🔧 Starting SAMFMS Maintenance Service..."

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export MAINTENANCE_SERVICE_PORT=21007
export DATABASE_MAINTENANCE=samfms_maintenance

# Check if required services are running
echo "📋 Checking dependencies..."

# Check MongoDB
if ! nc -z localhost 21003; then
    echo "❌ MongoDB not accessible on port 21003"
    exit 1
fi
echo "✅ MongoDB is running"

# Check RabbitMQ
if ! nc -z localhost 21000; then
    echo "❌ RabbitMQ not accessible on port 21000"
    exit 1
fi
echo "✅ RabbitMQ is running"

# Start maintenance service
echo "🚀 Starting maintenance service..."
cd Sblocks/maintenance
python main.py

echo "🔧 Maintenance service started on port 21007"
"""
        
        script_file = self.base_path / "start_maintenance_service.sh"
        with open(script_file, 'w') as f:
            f.write(script_content)
            
        # Make executable
        os.chmod(script_file, 0o755)
        
        self.fixes_applied.append("Created startup script: start_maintenance_service.sh")
        print("✅ Startup script created")
        
    def run_all_fixes(self):
        """Run all configuration fixes"""
        print("🔧 SAMFMS Maintenance Service Configuration Fixer")
        print("=" * 50)
        
        self.fix_environment_variables()
        self.fix_main_py_configuration()
        self.create_missing_directories()
        self.validate_docker_configuration()
        self.generate_startup_script()
        
        print("\n📋 FIXES APPLIED:")
        if self.fixes_applied:
            for fix in self.fixes_applied:
                print(f"  ✅ {fix}")
        else:
            print("  ✅ No fixes needed - configuration is correct")
            
        print("\n🔍 CONNECTIVITY CHECK:")
        
    def run_connectivity_check(self):
        """Run connectivity validation"""
        self.validate_service_connectivity()
        
        print("\n🚀 STARTUP INSTRUCTIONS:")
        print("1. Start MongoDB: docker-compose up mongodb")
        print("2. Start RabbitMQ: docker-compose up rabbitmq")
        print("3. Start Core Service: docker-compose up core")
        print("4. Start Maintenance Service: ./start_maintenance_service.sh")
        print("5. Run tests: python test_maintenance_service.py")

def main():
    fixer = MaintenanceServiceFixer()
    fixer.run_all_fixes()
    fixer.run_connectivity_check()

if __name__ == "__main__":
    main()
