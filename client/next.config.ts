import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images:{remotePatterns:[
    {
      hostname:'cdn.prod.website-files.com',
              protocol: 'https',

    }
  ]
  }
};

export default nextConfig;
