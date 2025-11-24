/** @type {import('next').NextConfig} */
const nextConfig = {
  // Remove rewrites for production - we'll use environment variables for backend URL
  // For local development, you can keep using rewrites or set NEXT_PUBLIC_API_URL
  async rewrites() {
    // Only use rewrites in development when API_URL is not set
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || process.env.API_URL
    if (!backendUrl && process.env.NODE_ENV === 'development') {
      return [
        {
          source: '/api/:path*',
          destination: 'http://localhost:5000/api/:path*', // Proxy to Backend in dev
        },
      ]
    }
    return []
  },
}

module.exports = nextConfig

