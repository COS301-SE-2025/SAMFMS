/**
 * Jest Configuration for Frontend API Testing
 * Configures Jest for testing API functions with container integration
 */
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/__tests__/api/setup.js'],
  testMatch: ['<rootDir>/src/__tests__/**/*.test.js', '<rootDir>/src/__tests__/**/*.test.jsx'],
  collectCoverageFrom: [
    'src/backend/api/**/*.js',
    'src/backend/services/**/*.js',
    'src/config/**/*.js',
    'src/lib/**/*.js',
    '!src/backend/api/index.js',
    '!**/node_modules/**',
    '!**/build/**',
    '!**/dist/**',
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
  moduleNameMapping: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2|mp4|webm|wav|mp3|m4a|aac|oga)$':
      '<rootDir>/src/__tests__/__mocks__/fileMock.js',
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@services/(.*)$': '<rootDir>/src/services/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1',
    '^@config/(.*)$': '<rootDir>/src/config/$1',
    '^@backend/(.*)$': '<rootDir>/src/backend/$1',
    '^@lib/(.*)$': '<rootDir>/src/lib/$1',
  },
  collectCoverageFrom: [
    'src/backend/**/*.{js,jsx,ts,tsx}',
    'src/services/**/*.{js,jsx,ts,tsx}',
    'src/lib/**/*.{js,jsx,ts,tsx}',
    'src/utils/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/serviceWorker.js',
    '!src/setupTests.js',
    '!src/reportWebVitals.js',
    '!src/index.js',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
  coverageReporters: ['text', 'lcov', 'html'],
  testTimeout: 30000,
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': 'babel-jest',
  },
  moduleFileExtensions: ['js', 'jsx', 'ts', 'tsx', 'json'],
  transformIgnorePatterns: ['node_modules/(?!(axios|@babel/runtime)/)'],
  globals: {
    'ts-jest': {
      tsconfig: 'tsconfig.json',
    },
  },
};
