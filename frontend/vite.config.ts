import path from "node:path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { "@": path.resolve(import.meta.dirname, "./src") },
  },
  server: {
    // Loopback only, and a fixed port because the backend allows exactly this CORS origin.
    host: "localhost",
    port: 5173,
    strictPort: true,
  },
})
