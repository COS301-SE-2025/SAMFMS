// MongoDB Initialization Script for SAMFMS
// This script creates databases and initial collections for the microservices

// List of databases to create
const databases = [
    'samfms_core',
    'samfms_gps',
    'samfms_trip_planning',
    'samfms_vehicle_maintenance',
    'samfms_security',
    'samfms_users',
    'samfms_vehicles',
    'samfms_management'
];

// Function to create database with initial collection
function createDatabaseWithCollection(dbName) {
    try {
        const db = db.getSiblingDB(dbName);
        
        // Create an initial collection to ensure database exists
        db.createCollection('_init', {
            comment: 'Initial collection to ensure database creation'
        });
        
        // Create indexes for common fields
        if (dbName.includes('gps')) {
            db.gps_data.createIndex({ "vehicle_id": 1, "timestamp": -1 });
            db.gps_data.createIndex({ "location": "2dsphere" });
        }
        
        if (dbName.includes('users')) {
            db.users.createIndex({ "email": 1 }, { unique: true });
            db.users.createIndex({ "username": 1 }, { unique: true });
        }
        
        if (dbName.includes('vehicles')) {
            db.vehicles.createIndex({ "vehicle_id": 1 }, { unique: true });
            db.vehicles.createIndex({ "license_plate": 1 }, { unique: true });
        }
        
        if (dbName.includes('security')) {
            db.sessions.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 });
            db.login_attempts.createIndex({ "ip_address": 1, "created_at": 1 });
        }
        
        print(`Database '${dbName}' created successfully with initial collections`);
        
    } catch (error) {
        print(`Error creating database '${dbName}': ${error}`);
    }
}

// Main execution
print('Starting SAMFMS MongoDB initialization...');

databases.forEach(dbName => {
    createDatabaseWithCollection(dbName);
});

// Create admin user if credentials are provided
if (process.env.MONGODB_USERNAME && process.env.MONGODB_PASSWORD) {
    try {
        const adminDb = db.getSiblingDB('admin');
        
        // Create application user with readWrite access to all SAMFMS databases
        adminDb.createUser({
            user: process.env.MONGODB_USERNAME,
            pwd: process.env.MONGODB_PASSWORD,
            roles: databases.map(dbName => ({
                role: 'readWrite',
                db: dbName
            })).concat([
                { role: 'dbAdmin', db: 'admin' }
            ])
        });
        
        print(`Application user '${process.env.MONGODB_USERNAME}' created successfully`);
        
    } catch (error) {
        print(`Note: User creation failed (user may already exist): ${error}`);
    }
}

print('SAMFMS MongoDB initialization completed');
