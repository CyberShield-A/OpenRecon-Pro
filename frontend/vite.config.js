import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        // Aligné sur le port interne 5000 de Flask
        target: "http://127.0.0.1:5000", 
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
