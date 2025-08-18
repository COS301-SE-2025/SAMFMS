#!/usr/bin/env python3
"""
Display current mock data generation configuration
"""

from config import *

def show_configuration():
    """Display current configuration settings"""
    print("🔧 SAMFMS Mock Data Generator - Configuration")
    print("=" * 50)
    print()
    
    print("📊 Data Generation Defaults:")
    print(f"   • Vehicles: 50")
    print(f"   • Drivers: 50") 
    print(f"   • Managers: 10")
    print(f"   • User Password: Password1!")
    print()
    
    print("⚡ Performance Settings:")
    print(f"   • Requests per minute: {REQUESTS_PER_MINUTE}")
    print(f"   • Delay between requests: {DELAY_BETWEEN_REQUESTS:.2f} seconds")
    print(f"   • Rate: {1/DELAY_BETWEEN_REQUESTS:.1f} requests/second")
    print()
    
    print("🌐 Service URLs:")
    print(f"   • Core Service: {CORE_BASE_URL}")
    print(f"   • Maintenance Service: {MAINTENANCE_BASE_URL}")
    print()
    
    print("🔐 Authentication:")
    print(f"   • Login Email: {LOGIN_EMAIL}")
    print(f"   • Password Source: {'Environment Variable' if LOGIN_PASSWORD != 'Password2@' else 'Default/Prompt'}")
    print()
    
    print("🚗 Sample Vehicle Configuration:")
    print(f"   • Vehicle Types: {len(VEHICLE_TYPES)} types")
    print(f"   • Vehicle Makes: {len(VEHICLE_MAKES)} makes")
    print(f"   • License Types: {len(LICENSE_TYPES)} license types")
    print()
    
    estimated_time_50_vehicles = (50 * DELAY_BETWEEN_REQUESTS + 4) / 60  # +4 seconds for batches
    estimated_time_50_users = (50 * DELAY_BETWEEN_REQUESTS + 4) / 60
    total_estimated = estimated_time_50_vehicles + estimated_time_50_users
    
    print("⏱️  Estimated Generation Times:")
    print(f"   • 50 vehicles: ~{estimated_time_50_vehicles:.1f} minutes")
    print(f"   • 50 drivers: ~{estimated_time_50_users:.1f} minutes") 
    print(f"   • 10 managers: ~{(10 * DELAY_BETWEEN_REQUESTS)/60:.1f} minutes")
    print(f"   • Total estimated: ~{total_estimated:.1f} minutes")
    print()

if __name__ == "__main__":
    show_configuration()
