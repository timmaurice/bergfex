import globals from 'globals';
import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import litPlugin from 'eslint-plugin-lit';
import wcPlugin from 'eslint-plugin-wc';
import prettierConfig from 'eslint-config-prettier';

export default tseslint.config(
  {
    ignores: ['node_modules/', 'custom_components/bergfex/bergfex-card.js', 'config/', 'venv/'],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['frontend/src/**/*.ts'],
    plugins: {
      lit: litPlugin,
      wc: wcPlugin,
    },
    rules: {
      ...litPlugin.configs.recommended.rules,
      ...wcPlugin.configs.recommended.rules,
    },
    languageOptions: {
      globals: {
        ...globals.browser,
      },
    },
  },
  prettierConfig,
);
