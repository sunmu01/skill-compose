/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable React strict mode for development
  reactStrictMode: true,

  // Output standalone for Docker deployment
  output: 'standalone',

  // Ignore ESLint errors during build (for Docker)
  eslint: {
    ignoreDuringBuilds: true,
  },

  // API proxy to backend
  // In development: proxy to localhost:8766
  // In Docker: use NEXT_PUBLIC_API_URL environment variable
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8766';
    return [
      {
        source: '/api/v1/:path*',
        destination: `${apiUrl}/api/v1/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
