import { fileURLToPath, URL } from "node:url";

import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [vue()],

  build: {
    // 使用库模式验证组件，不需要创建真实页面。
    lib: {
      entry: fileURLToPath(new URL("./src/index.ts", import.meta.url)),

      name: "MigrationCandidate",
      formats: ["es"],
      fileName: "migration-candidate",
    },

    outDir: "dist",
    emptyOutDir: true,

    rollupOptions: {
      // Vue 不打入验证产物。
      external: ["vue"],
    },
  },
});
