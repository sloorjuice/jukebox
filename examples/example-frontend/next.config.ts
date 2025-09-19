/**import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  allowedDevOrigins: [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://jukebox.local:3000',
    'http://jukebox.local:3000/'
  ],
};

export default nextConfig;**/

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  allowedDevOriginPattern: /^http:\/\/(localhost|127\.0\.0\.1|jukebox\.local)(:\d+)?\/?$/, //Allows any port
};

export default nextConfig;