/**
 * API Configuration
 * Centralized API base URL configuration for making requests to the backend
 */

// Get the API base URL from environment variables
// NEXT_PUBLIC_ prefix makes it available on both client and server side
const getApiBaseUrl = (): string => {
  // NEXT_PUBLIC_ variables are available on both client and server
  // They are replaced at build time with their actual values
  if (typeof process !== 'undefined' && process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL
  }
  return ''
}

// Base URL for API requests
export const API_BASE_URL = getApiBaseUrl()

/**
 * Get the full API URL for a given endpoint
 * If API_BASE_URL is set, use it. Otherwise, use relative paths (for rewrites/proxy)
 */
export const getApiUrl = (endpoint: string): string => {
  // Remove leading slash if present to avoid double slashes
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint
  
  if (API_BASE_URL) {
    // Ensure API_BASE_URL doesn't end with a slash
    const baseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL
    
    // Check if baseUrl already includes /api
    if (baseUrl.endsWith('/api')) {
      return `${baseUrl}/${cleanEndpoint}`
    }
    
    // Otherwise, add /api prefix (backend routes are at /api/*)
    return `${baseUrl}/api/${cleanEndpoint}`
  }
  
  // Fallback to relative path (will use Next.js rewrites in dev or same-origin in prod)
  return `/api/${cleanEndpoint}`
}

