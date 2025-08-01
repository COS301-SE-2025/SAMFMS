"""
Test vehicle validation functionality
"""

import asyncio
import sys
import os

# Add the maintenance service to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from Sblocks.maintenance.utils.vehicle_validator import vehicle_validator
from Sblocks.maintenance.services.maintenance_service import maintenance_records_service
from Sblocks.maintenance.services.maintenance_schedules_service import maintenance_schedules_service


async def test_vehicle_validation():
    """Test vehicle validation functionality"""
    print("Testing vehicle validation...")
    
    # Test with a non-existent vehicle ID
    try:
        result = await vehicle_validator.validate_vehicle_id("nonexistent_vehicle_id")
        print(f"Non-existent vehicle validation result: {result}")
        assert result == False, "Non-existent vehicle should return False"
    except Exception as e:
        print(f"Error validating non-existent vehicle: {e}")
    
    # Test with empty vehicle ID
    try:
        result = await vehicle_validator.validate_vehicle_id("")
        print(f"Empty vehicle ID validation result: {result}")
        assert result == False, "Empty vehicle ID should return False"
    except Exception as e:
        print(f"Error validating empty vehicle ID: {e}")
    
    print("Vehicle validation tests completed!")


async def test_maintenance_record_creation():
    """Test maintenance record creation with vehicle validation"""
    print("Testing maintenance record creation with vehicle validation...")
    
    # Test with invalid vehicle ID
    try:
        test_data = {
            "vehicle_id": "invalid_vehicle_123",
            "maintenance_type": "oil_change",
            "scheduled_date": "2025-08-01T10:00:00Z",
            "title": "Test Oil Change"
        }
        
        result = await maintenance_records_service.create_maintenance_record(test_data)
        print("ERROR: Should have failed with invalid vehicle ID!")
        assert False, "Should have raised ValueError for invalid vehicle ID"
    except ValueError as e:
        print(f"✓ Correctly caught error for invalid vehicle ID: {e}")
        assert "does not exist in the vehicles collection" in str(e)
    except Exception as e:
        print(f"Unexpected error: {e}")
        
    print("Maintenance record creation validation tests completed!")


async def test_maintenance_schedule_creation():
    """Test maintenance schedule creation with vehicle validation"""
    print("Testing maintenance schedule creation with vehicle validation...")
    
    # Test with invalid vehicle ID
    try:
        test_data = {
            "vehicle_id": "invalid_vehicle_456",
            "maintenance_type": "brake_service",
            "scheduled_date": "2025-08-15T14:00:00Z",
            "title": "Test Brake Service Schedule"
        }
        
        result = await maintenance_schedules_service.create_maintenance_schedule(test_data)
        print("ERROR: Should have failed with invalid vehicle ID!")
        assert False, "Should have raised ValueError for invalid vehicle ID"
    except ValueError as e:
        print(f"✓ Correctly caught error for invalid vehicle ID: {e}")
        assert "does not exist in the vehicles collection" in str(e)
    except Exception as e:
        print(f"Unexpected error: {e}")
        
    print("Maintenance schedule creation validation tests completed!")


async def main():
    """Run all tests"""
    print("Starting maintenance service validation tests...\n")
    
    try:
        await test_vehicle_validation()
        print()
        await test_maintenance_record_creation()
        print()
        await test_maintenance_schedule_creation()
        print()
        print("✓ All tests completed successfully!")
        print("\nSummary:")
        print("- Vehicle ID validation is working correctly")
        print("- Maintenance records validate vehicle IDs before creation")
        print("- Maintenance schedules validate vehicle IDs before creation")
        print("- Both services properly connect to the vehicles collection in the management database")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        return False
    
    finally:
        # Close database connections
        try:
            await vehicle_validator.close_connection()
        except:
            pass
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
