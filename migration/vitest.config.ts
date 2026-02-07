import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['migration/tests/**/*.test.ts'],
    root: '..',
  },
});
