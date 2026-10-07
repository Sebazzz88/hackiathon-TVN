import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// El proxy apunta a 127.0.0.1 (IPv4) y no a "localhost": en Windows/Node "localhost" puede resolverse a ::1 (IPv6)
// mientras uvicorn escucha en IPv4, y el proxy devolvía errores 500 esporádicos al interfaz.
// Los tiempos máximos son de 10 min (igual que LLM_TIMEOUT): un borrador con IA local puede tardar más de 2 min.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": { target: "http://127.0.0.1:8000", changeOrigin: false, timeout: 600000, proxyTimeout: 600000 }, "/health": "http://127.0.0.1:8000" } },
});
