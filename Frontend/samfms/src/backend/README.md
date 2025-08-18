# Backend API Organization

This document describes the improved organization of the SAMFMS Frontend backend API layer after the refactoring completed in steps 1-4.

## Overview

The backend folder has been restructured to provide better organization, maintainability, and developer experience. The new structure follows a modular approach with clear separation of concerns.

## Directory Structure

```
backend/
├── api/                          # Domain-specific API modules
│   ├── index.js                  # Main export file for all APIs
│   ├── auth.js                   # Authentication & user management
│   ├── analytics.js              # Analytics and reporting
│   ├── plugins.js                # Plugin management
│   ├── vehicles.js               # Vehicle management (NEW)
│   ├── drivers.js                # Driver management (NEW)
│   ├── assignments.js            # Vehicle assignment management (NEW)
│   └── invitations.js            # User invitation management (NEW)
├── services/                     # Core services (NEW)
│   ├── httpClient.js            # Centralized HTTP client with error handling
│   └── errorHandler.js          # Standardized error handling utilities
├── API.js                       # Legacy compatibility layer (DEPRECATED)
└── API.ts                       # TypeScript API file (TO BE REMOVED)
```

## Key Improvements

### 1. Centralized HTTP Client (`services/httpClient.js`)

- **Automatic token management**: Handles authentication tokens automatically
- **Token refresh**: Automatically refreshes expired tokens
- **Retry logic**: Retries failed requests with exponential backoff
- **Timeout handling**: Configurable request timeouts
- **Standardized error handling**: Consistent error responses across all APIs

```javascript
import { httpClient } from '../backend/services/httpClient';

// Simple usage - authentication and error handling is automatic
const vehicles = await httpClient.get('/vehicles');
const newVehicle = await httpClient.post('/vehicles', vehicleData);
```

### 2. Domain-Specific API Modules

Each domain has its own dedicated module with clear, focused responsibilities:

#### Vehicles API (`api/vehicles.js`)

- `createVehicle(vehicleData)`
- `getVehicles(params)`
- `getVehicle(vehicleId)`
- `updateVehicle(vehicleId, updateData)`
- `deleteVehicle(vehicleId)`
- `searchVehicles(query)`

#### Drivers API (`api/drivers.js`)

- `createDriver(driverData)`
- `getDrivers(params)`
- `getDriver(driverId)`
- `updateDriver(driverId, updateData)`
- `deleteDriver(driverId)`
- `searchDrivers(query)`

#### Assignments API (`api/assignments.js`)

- `getVehicleAssignments(params)`
- `createVehicleAssignment(assignmentData)`
- `updateVehicleAssignment(assignmentId, updateData)`
- `deleteVehicleAssignment(assignmentId)`

#### Invitations API (`api/invitations.js`)

- `sendInvitation(invitationData)`
- `getPendingInvitations()`
- `resendInvitation(email)`
- `cancelInvitation(email)`
- `verifyInvitationOTP(email, otp)`
- `completeUserRegistration(email, otp, username, password)`

### 3. Standardized Error Handling (`services/errorHandler.js`)

- **Custom Error Classes**: `ApiError`, `ValidationError`, `NetworkError`, `TimeoutError`
- **Error Classification**: Automatic categorization of client vs server errors
- **User-Friendly Messages**: Converts technical errors to user-friendly messages
- **Retry Logic**: Determines which errors are retryable
- **Logging**: Centralized error logging for debugging

```javascript
import { ApiError, createErrorResponse } from '../backend/services/errorHandler';

try {
  const result = await httpClient.get('/vehicles');
} catch (error) {
  if (error instanceof ApiError) {
    console.log('Status:', error.status);
    console.log('User message:', error.getUserMessage());
    console.log('Is retryable:', error.isRetryableError());
  }
}
```

### 4. Updated Configuration

The API configuration has been enhanced to include missing endpoints and provide better organization.

## Migration Guide

### For New Code

Use the modular imports for better tree-shaking and clearer dependencies:

```javascript
// Recommended - Import specific functions
import { getVehicles, createVehicle } from '../backend/api/vehicles';
import { getDrivers } from '../backend/api/drivers';

// Alternative - Import from main API index
import { getVehicles, getDrivers } from '../backend/api';
```

### For Existing Code

The legacy `API.js` file provides backward compatibility, but shows deprecation warnings:

```javascript
// Still works but deprecated
import { getVehicles } from '../backend/API';
```

### Migration Steps

1. **Replace imports**: Change from `../backend/API` to specific modules
2. **Remove manual error handling**: The new HTTP client handles errors automatically
3. **Remove manual token management**: Authentication is handled automatically
4. **Update error handling**: Use the new error classes and utilities

### Example Migration

**Before:**

```javascript
import { getVehicles, getToken } from '../backend/API';

const fetchVehicles = async () => {
  try {
    const token = getToken();
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch('/vehicles', {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch vehicles');
    }

    return await response.json();
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
};
```

**After:**

```javascript
import { getVehicles } from '../backend/api/vehicles';

const fetchVehicles = async () => {
  try {
    return await getVehicles();
  } catch (error) {
    // Error handling is centralized and standardized
    console.error('Error:', error.getUserMessage());
    throw error;
  }
};
```

## Benefits

1. **Better Organization**: Clear separation by domain/functionality
2. **Reduced Code Duplication**: Centralized HTTP client and error handling
3. **Improved Maintainability**: Modular structure makes changes easier
4. **Better Testing**: Smaller, focused modules are easier to test
5. **Type Safety**: Better IntelliSense and potential for TypeScript migration
6. **Consistent Error Handling**: Standardized error responses across the app
7. **Automatic Token Management**: No more manual token handling
8. **Retry Logic**: Automatic retry for transient failures

## Next Steps

1. **Complete Plugin Migration**: Update remaining plugin functions to use HTTP client
2. **Remove Legacy Files**: Remove `API.ts` and eventually deprecate `API.js`
3. **Add TypeScript**: Gradually migrate to TypeScript for better type safety
4. **Add Caching**: Implement response caching for frequently accessed data
5. **Add Testing**: Write comprehensive tests for all API modules
6. **Add Documentation**: Generate API documentation from JSDoc comments

## Breaking Changes

None. The refactoring maintains full backward compatibility through the legacy `API.js` file.

## Support

For questions or issues with the new API structure, please refer to this documentation or contact the development team.
