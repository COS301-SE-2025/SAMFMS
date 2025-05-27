// MongoDB initialization script for GPS tracking service
// This script creates the database, collections, and indexes for optimal performance

print('Starting GPS service database initialization...');

// Switch to the GPS database
db = db.getSiblingDB('gps_tracking');

// Create collections
db.createCollection('vehicle_locations');
db.createCollection('location_history');
db.createCollection('geofences');
db.createCollection('geofence_events');
db.createCollection('routes');
db.createCollection('route_tracking');

print('Collections created successfully');

// Create indexes for vehicle_locations collection
db.vehicle_locations.createIndex({ "vehicle_id": 1 }, { unique: true });
db.vehicle_locations.createIndex({ "location.coordinates": "2dsphere" });
db.vehicle_locations.createIndex({ "timestamp": 1 });
db.vehicle_locations.createIndex({ "driver_id": 1 });

print('Indexes created for vehicle_locations collection');

// Create indexes for location_history collection
db.location_history.createIndex({ "vehicle_id": 1, "timestamp": -1 });
db.location_history.createIndex({ "location.coordinates": "2dsphere" });
db.location_history.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 7776000 }); // 90 days TTL
db.location_history.createIndex({ "driver_id": 1 });
db.location_history.createIndex({ "trip_id": 1 });

print('Indexes created for location_history collection');

// Create indexes for geofences collection
db.geofences.createIndex({ "name": 1 });
db.geofences.createIndex({ "geometry": "2dsphere" });
db.geofences.createIndex({ "is_active": 1 });
db.geofences.createIndex({ "geofence_type": 1 });
db.geofences.createIndex({ "created_by": 1 });

print('Indexes created for geofences collection');

// Create indexes for geofence_events collection
db.geofence_events.createIndex({ "vehicle_id": 1, "timestamp": -1 });
db.geofence_events.createIndex({ "geofence_id": 1, "timestamp": -1 });
db.geofence_events.createIndex({ "event_type": 1 });
db.geofence_events.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 15552000 }); // 180 days TTL
db.geofence_events.createIndex({ "driver_id": 1 });

print('Indexes created for geofence_events collection');

// Create indexes for routes collection
db.routes.createIndex({ "name": 1 });
db.routes.createIndex({ "start_location.coordinates": "2dsphere" });
db.routes.createIndex({ "end_location.coordinates": "2dsphere" });
db.routes.createIndex({ "is_active": 1 });
db.routes.createIndex({ "created_by": 1 });

print('Indexes created for routes collection');

// Create indexes for route_tracking collection
db.route_tracking.createIndex({ "vehicle_id": 1, "timestamp": -1 });
db.route_tracking.createIndex({ "route_id": 1, "timestamp": -1 });
db.route_tracking.createIndex({ "trip_id": 1 });
db.route_tracking.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 7776000 }); // 90 days TTL
db.route_tracking.createIndex({ "driver_id": 1 });

print('Indexes created for route_tracking collection');

// Create compound indexes for common queries
db.location_history.createIndex({ "vehicle_id": 1, "trip_id": 1, "timestamp": -1 });
db.geofence_events.createIndex({ "vehicle_id": 1, "geofence_id": 1, "timestamp": -1 });
db.route_tracking.createIndex({ "route_id": 1, "vehicle_id": 1, "timestamp": -1 });

print('Compound indexes created successfully');

// Create text indexes for search functionality
db.geofences.createIndex({ "name": "text", "description": "text" });
db.routes.createIndex({ "name": "text", "description": "text" });

print('Text indexes created for search functionality');

// Insert sample geofences for testing
db.geofences.insertMany([
    {
        "_id": ObjectId(),
        "name": "Main Depot",
        "description": "Primary vehicle depot and maintenance facility",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-122.4194, 37.7749],
                [-122.4184, 37.7749],
                [-122.4184, 37.7759],
                [-122.4194, 37.7759],
                [-122.4194, 37.7749]
            ]]
        },
        "geofence_type": "depot",
        "is_active": true,
        "created_by": "system",
        "created_at": new Date(),
        "updated_at": new Date(),
        "metadata": {
            "capacity": 50,
            "operating_hours": "06:00-22:00"
        }
    },
    {
        "_id": ObjectId(),
        "name": "Downtown Delivery Zone",
        "description": "High-priority delivery area in downtown",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-122.4094, 37.7849],
                [-122.4044, 37.7849],
                [-122.4044, 37.7899],
                [-122.4094, 37.7899],
                [-122.4094, 37.7849]
            ]]
        },
        "geofence_type": "delivery_zone",
        "is_active": true,
        "created_by": "system",
        "created_at": new Date(),
        "updated_at": new Date(),
        "metadata": {
            "priority": "high",
            "time_restrictions": "07:00-19:00"
        }
    }
]);

print('Sample geofences inserted');

// Insert sample routes for testing
db.routes.insertMany([
    {
        "_id": ObjectId(),
        "name": "Downtown Express Route",
        "description": "Fast route to downtown delivery zone",
        "start_location": {
            "type": "Point",
            "coordinates": [-122.4194, 37.7749]
        },
        "end_location": {
            "type": "Point",
            "coordinates": [-122.4069, 37.7874]
        },
        "waypoints": [
            {
                "type": "Point",
                "coordinates": [-122.4150, 37.7800]
            },
            {
                "type": "Point",
                "coordinates": [-122.4120, 37.7830]
            }
        ],
        "estimated_duration": 1800,
        "estimated_distance": 5.2,
        "is_active": true,
        "created_by": "system",
        "created_at": new Date(),
        "updated_at": new Date(),
        "metadata": {
            "traffic_pattern": "normal",
            "road_conditions": "good"
        }
    }
]);

print('Sample routes inserted');

// Create user for the GPS service (optional, for production)
try {
    db.createUser({
        user: "gps_service",
        pwd: "gps_service_password",
        roles: [
            { role: "readWrite", db: "gps_tracking" }
        ]
    });
    print('GPS service user created');
} catch (e) {
    print('User creation skipped (may already exist): ' + e.message);
}

print('GPS service database initialization completed successfully!');
print('Collections created: vehicle_locations, location_history, geofences, geofence_events, routes, route_tracking');
print('Indexes created for optimal performance');
print('Sample data inserted for testing');
