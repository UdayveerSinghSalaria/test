import type { NextConfig } from "next";

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // Proxy all API calls to FastAPI. This keeps the browser on a single
  // origin (localhost:3000), so the httpOnly session cookie works with
  // SameSite=Lax and no CORS credentials edge cases arise.
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${BACKEND}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
