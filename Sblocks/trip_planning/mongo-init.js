// MongoDB initialization script for Trip Planning Service
// This script creates indexes and initial data

// Connect to the trip_planning_db database
db = db.getSiblingDB('trip_planning_db');

// Create collections with indexes

// Trips collection indexes
db.trips.createIndex({ status: 1 });
db.trips.createIndex({ scheduled_start_time: 1 });
db.trips.createIndex({ driver_id: 1 });
db.trips.createIndex({ vehicle_id: 1 });
db.trips.createIndex({ route_id: 1 });
db.trips.createIndex({ created_at: -1 });
db.trips.createIndex({
  'origin.latitude': 1,
  'origin.longitude': 1,
});
db.trips.createIndex({
  'destination.latitude': 1,
  'destination.longitude': 1,
});

// Vehicles collection indexes
db.vehicles.createIndex({ license_plate: 1 }, { unique: true });
db.vehicles.createIndex({ status: 1 });
db.vehicles.createIndex({ vehicle_type: 1 });
db.vehicles.createIndex({
  'current_location.latitude': 1,
  'current_location.longitude': 1,
});
db.vehicles.createIndex({ last_maintenance_date: 1 });
db.vehicles.createIndex({ next_maintenance_due: 1 });

// Drivers collection indexes
db.drivers.createIndex({ employee_id: 1 }, { unique: true });
db.drivers.createIndex({ email: 1 }, { unique: true });
db.drivers.createIndex({ status: 1 });
db.drivers.createIndex({ 'license.license_type': 1 });
db.drivers.createIndex({ 'license.expiry_date': 1 });
db.drivers.createIndex({
  'current_location.latitude': 1,
  'current_location.longitude': 1,
});

// Routes collection indexes
db.routes.createIndex({ name: 1 });
db.routes.createIndex({ total_distance: 1 });
db.routes.createIndex({ estimated_duration: 1 });
db.routes.createIndex({ created_at: -1 });

// Schedules collection indexes
db.schedules.createIndex({ trip_id: 1 });
db.schedules.createIndex({ vehicle_id: 1 });
db.schedules.createIndex({ driver_id: 1 });
db.schedules.createIndex({ scheduled_start_time: 1 });
db.schedules.createIndex({ scheduled_end_time: 1 });
db.schedules.createIndex({ status: 1 });

// Compound indexes for complex queries
db.trips.createIndex({
  status: 1,
  scheduled_start_time: 1,
});
db.vehicles.createIndex({
  status: 1,
  vehicle_type: 1,
});
db.drivers.createIndex({
  status: 1,
  'license.license_type': 1,
});
db.schedules.createIndex({
  vehicle_id: 1,
  scheduled_start_time: 1,
  scheduled_end_time: 1,
});
db.schedules.createIndex({
  driver_id: 1,
  scheduled_start_time: 1,
  scheduled_end_time: 1,
});

print('Trip Planning Database initialized with indexes');

// Insert sample data for testing (optional)
print('Inserting sample data...');

// Sample vehicles
db.vehicles.insertMany([
  {
    _id: ObjectId(),
    license_plate: 'ABC-123',
    make: 'Toyota',
    model: 'Hiace',
    year: 2022,
    vehicle_type: 'van',
    capacity: 15,
    status: 'available',
    fuel_efficiency: 12.5,
    current_location: {
      latitude: 14.5995,
      longitude: 120.9842,
      timestamp: new Date(),
    },
    created_at: new Date(),
    updated_at: new Date(),
  },
  {
    _id: ObjectId(),
    license_plate: 'XYZ-789',
    make: 'Isuzu',
    model: 'Traviz',
    year: 2021,
    vehicle_type: 'bus',
    capacity: 30,
    status: 'available',
    fuel_efficiency: 8.5,
    current_location: {
      latitude: 14.6091,
      longitude: 121.0223,
      timestamp: new Date(),
    },
    created_at: new Date(),
    updated_at: new Date(),
  },
]);

// Sample drivers
db.drivers.insertMany([
  {
    _id: ObjectId(),
    employee_id: 'DRV001',
    first_name: 'Juan',
    last_name: 'Santos',
    email: 'juan.santos@example.com',
    phone: '+63-912-345-6789',
    status: 'available',
    license: {
      license_number: 'D12-34-567890',
      license_type: 'professional',
      expiry_date: new Date('2026-05-26'),
    },
    hire_date: new Date('2023-01-15'),
    current_location: {
      latitude: 14.5995,
      longitude: 120.9842,
      timestamp: new Date(),
    },
    performance_metrics: [],
    created_at: new Date(),
    updated_at: new Date(),
  },
  {
    _id: ObjectId(),
    employee_id: 'DRV002',
    first_name: 'Maria',
    last_name: 'Cruz',
    email: 'maria.cruz@example.com',
    phone: '+63-917-876-5432',
    status: 'available',
    license: {
      license_number: 'D98-76-543210',
      license_type: 'professional',
      expiry_date: new Date('2025-12-31'),
    },
    hire_date: new Date('2022-06-10'),
    current_location: {
      latitude: 14.6091,
      longitude: 121.0223,
      timestamp: new Date(),
    },
    performance_metrics: [],
    created_at: new Date(),
    updated_at: new Date(),
  },
]);

// Sample routes
db.routes.insertMany([
  {
    _id: ObjectId(),
    name: 'Manila to Quezon City',
    description: 'Main route from Manila to Quezon City',
    waypoints: [
      {
        name: 'Manila City Hall',
        latitude: 14.5995,
        longitude: 120.9842,
        order: 1,
      },
      {
        name: 'Quezon Memorial Circle',
        latitude: 14.676,
        longitude: 121.0437,
        order: 2,
      },
    ],
    total_distance: 15.2,
    estimated_duration: 1.5,
    created_at: new Date(),
    updated_at: new Date(),
  },
]);

print('Sample data inserted successfully');
print('Trip Planning Database setup completed!');
