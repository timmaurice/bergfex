import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './frontend/test/setup.ts',
    alias: { '\\.scss$': './frontend/test/styleMock.ts' },
  },
});
