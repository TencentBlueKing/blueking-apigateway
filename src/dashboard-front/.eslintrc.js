module.exports = {
  root: true,
  extends: ['@blueking/eslint-config-bk/tsvue3'],
  parser: 'vue-eslint-parser',
  parserOptions: {
    project: './tsconfig.eslint.json',
    tsconfigRootDir: __dirname,
    sourceType: 'module',
    parser: '@typescript-eslint/parser',
    ecmaFeatures: {
      jsx: true,
    },
    ecmaVersion: 13,
  },
  rules: {
    'no-param-reassign': 0,
    'arrow-body-style': 'off',
    '@typescript-eslint/naming-convention': 0,
    '@typescript-eslint/no-misused-promises': 0,
    'prefer-spread': 'off',
    'vue/multi-word-component-names': 'off',
  },
};
