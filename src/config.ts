/**
 * Application configuration
 * Environment variables for Vite should be prefixed with VITE_
 */

const config = {
  // API Base URL - defaults to localhost for development
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  
  // Frontend URL - used for redirects, etc.
  FRONTEND_URL: import.meta.env.VITE_FRONTEND_URL || 'http://localhost:5173',
  
  // Development mode check
  IS_DEVELOPMENT: import.meta.env.DEV,
  
  // Production mode check  
  IS_PRODUCTION: import.meta.env.PROD,
} as const;

// Validate required environment variables in production
if (config.IS_PRODUCTION) {
  if (!import.meta.env.VITE_API_BASE_URL) {
    console.warn('VITE_API_BASE_URL not set in production environment');
  }
}

export default config;