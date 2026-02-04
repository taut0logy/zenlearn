import type { NextConfig } from "next";

const nextConfig: any = {
  /* config options here */
 // output: "standalone",
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",//.supabase.co",
        // port: "",
        // pathname: "/**",
      },
      {
        protocol: "http",
        hostname: "**",//.supabase.co",
        // port: "",
        // pathname: "/**",
      },
    ],
  },
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },
};

export default nextConfig;
