import { globalIgnores } from 'eslint/config';
import {
  configureVueProject,
  defineConfigWithVueTs,
  vueTsConfigs,
} from '@vue/eslint-config-typescript';
import pluginVue from 'eslint-plugin-vue';
import pluginOxlint from 'eslint-plugin-oxlint';
import stylistic from '@stylistic/eslint-plugin';

configureVueProject({ scriptLangs: ['ts', 'tsx'] });

export default defineConfigWithVueTs(
  {
    name: 'app/files-to-lint',
    files: ['**/*.{ts,mts,tsx,vue}'],
  },

  globalIgnores([
    '**/dist/**',
    '**/dist-ssr/**',
    '**/coverage/**',
    '**/lib/**',
  ]),

  pluginVue.configs['flat/essential'],
  pluginVue.configs['flat/strongly-recommended'],
  pluginVue.configs['flat/recommended'],
  vueTsConfigs.recommended,
  ...pluginOxlint.configs['flat/recommended'],
  stylistic.configs.recommended,

  {
    plugins: { '@stylistic': stylistic },
    rules: {
      // TypeScript
      '@typescript-eslint/no-explicit-any': 'off',
      // ESLint
      'no-duplicate-imports': 'error',
      'sort-imports': ['error', { ignoreDeclarationSort: true }],
      // ESLint - stylistic
      '@stylistic/semi': ['error', 'always'],
      '@stylistic/comma-dangle': ['error', 'always-multiline'],
      // 'comma-spacing': ['error', { before: false, after: true }],
      '@stylistic/quotes': ['error', 'single'],
      '@stylistic/indent': ['error', 2],
      '@stylistic/max-len': ['error',
        {
          code: 120,
          ignoreComments: true,
          ignoreUrls: true,
          ignoreStrings: true,
          ignoreTemplateLiterals: true,
          ignoreRegExpLiterals: true,
        }],
      '@stylistic/object-property-newline': ['error'],
      '@stylistic/object-curly-newline': ['error', { multiline: true }],
      '@stylistic/curly-newline': ['error', 'always'],
      '@stylistic/array-bracket-newline': ['error', 'consistent'],
      '@stylistic/array-element-newline': ['error',
        {
          multiline: true,
          consistent: true,
        }],
      // Vue
      'vue/component-name-in-template-casing': 'error',
      'vue/define-emits-declaration': ['error', 'type-literal'],
      'vue/define-macros-order': [
        'error',
        {
          order: [
            'defineOptions',
            'defineModel',
            'defineProps',
            'defineEmits',
            'defineSlots',
          ],
          defineExposeLast: true,
        },
      ],
      'vue/define-props-destructuring': 'error',
      'vue/html-comment-content-spacing': 'error',
      'vue/html-comment-indent': 'error',
      'vue/no-empty-component-block': 'off',
      'vue/no-import-compiler-macros': 'error',
      'vue/no-root-v-if': 'error',
      'vue/no-unused-emit-declarations': 'error',
      'vue/no-unused-refs': 'error',
      'vue/no-use-v-else-with-v-for': 'error',
      'vue/no-useless-mustaches': 'error',
      'vue/padding-line-between-blocks': 'error',
      'vue/padding-lines-in-component-definition': 'error',
      'vue/prefer-separate-static-class': 'error',
      'vue/prefer-true-attribute-shorthand': 'error',
      'vue/multi-word-component-names': 'off',
    },
  },
);
