import path from "node:path";

import { defineConfig } from "vitest/config";

const root = import.meta.dirname;

export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(root, "src"),
      // `server-only` lanza un error fuera de Next.js; en las pruebas se reemplaza por un módulo vacío.
      "server-only": path.resolve(root, "vitest.server-only.ts"),
    },
  },
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
