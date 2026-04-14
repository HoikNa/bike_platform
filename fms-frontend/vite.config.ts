import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"
import { fileURLToPath, URL } from "node:url"

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      // "@/..." → "src/..." 경로 별칭
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      // 개발 환경에서 CORS 우회: /api/* → 백엔드 서버
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
})
