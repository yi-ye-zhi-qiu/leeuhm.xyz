import react, { reactCompilerPreset } from "@vitejs/plugin-react";
import babel from "@rolldown/plugin-babel";
import { defineConfig } from "vite";
import { resolve } from "path";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), babel({ presets: [reactCompilerPreset()] })],
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, "index.html"),
        player: resolve(__dirname, "player.html"),
        leaderboard: resolve(__dirname, "leaderboard.html"),
      },
    },
  },
});
