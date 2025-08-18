// Export all authentication-related functionality
export * from './auth';

// Export plugin-related functionality
export * from './plugins';

// Export vehicle management functionality
export * from './vehicles';

// Export driver management functionality
export * from './drivers';

// Export assignment management functionality
export * from './assignments';

// Export invitation management functionality
export * from './invitations';

// Export analytics functionality
export * from './analytics';

// Export maintenance functionality
export * from './maintenance';

// Export services
export { httpClient } from '../services/httpClient';
export * from '../services/errorHandler';

// This index file allows us to import from 'backend/api' rather than specific files
