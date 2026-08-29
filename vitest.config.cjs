const { defineConfig } = require("vitest/config");

module.exports = defineConfig({
  test: {
    include: ["**/tests/**/*.test.ts", "**/src/**/*.test.ts"],
    exclude: ["**/node_modules/**", "tests/e2e/**", "apps/**"],
  },
});
