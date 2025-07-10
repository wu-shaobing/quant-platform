import { defineConfig } from 'eslint-define-config';
import vue from 'eslint-plugin-vue';
import typescript from '@typescript-eslint/eslint-plugin';
import typescriptParser from '@typescript-eslint/parser';
import prettier from 'eslint-plugin-prettier';
export default defineConfig([
    {
        files: ['**/*.{js,jsx,ts,tsx,vue}'],
        languageOptions: {
            ecmaVersion: 2022,
            sourceType: 'module',
            parser: typescriptParser,
            parserOptions: {
                ecmaFeatures: {
                    jsx: true
                },
                extraFileExtensions: ['.vue']
            }
        },
        plugins: {
            vue: vue,
            '@typescript-eslint': typescript,
            prettier: prettier
        },
        rules: {
            // Vue 规则
            'vue/multi-word-component-names': 'error',
            'vue/component-definition-name-casing': ['error', 'PascalCase'],
            'vue/component-name-in-template-casing': ['error', 'kebab-case'],
            'vue/component-tags-order': ['error', {
                    order: ['script', 'template', 'style']
                }],
            'vue/block-tag-newline': ['error', {
                    singleline: 'always',
                    multiline: 'always'
                }],
            'vue/component-api-style': ['error', ['script-setup']],
            'vue/define-macros-order': ['error', {
                    order: ['defineOptions', 'defineProps', 'defineEmits', 'defineSlots']
                }],
            'vue/no-ref-as-operand': 'error',
            'vue/no-undef-components': 'error',
            'vue/no-undef-properties': 'error',
            'vue/no-unused-refs': 'error',
            'vue/prefer-separate-static-class': 'error',
            'vue/prefer-true-attribute-shorthand': 'error',
            'vue/require-macro-variable-name': ['error', {
                    defineProps: 'props',
                    defineEmits: 'emit',
                    defineSlots: 'slots',
                    useSlots: 'slots',
                    useAttrs: 'attrs'
                }],
            // TypeScript 规则
            '@typescript-eslint/no-unused-vars': ['error', {
                    argsIgnorePattern: '^_',
                    varsIgnorePattern: '^_'
                }],
            '@typescript-eslint/explicit-function-return-type': 'off',
            '@typescript-eslint/explicit-module-boundary-types': 'off',
            '@typescript-eslint/no-explicit-any': 'error',
            '@typescript-eslint/no-non-null-assertion': 'warn',
            '@typescript-eslint/prefer-optional-chain': 'error',
            '@typescript-eslint/prefer-nullish-coalescing': 'error',
            '@typescript-eslint/prefer-ts-expect-error': 'error',
            '@typescript-eslint/ban-ts-comment': ['error', {
                    'ts-expect-error': 'allow-with-description',
                    'ts-ignore': false,
                    'ts-nocheck': false,
                    'ts-check': false
                }],
            '@typescript-eslint/consistent-type-imports': 'error',
            '@typescript-eslint/consistent-type-definitions': ['error', 'interface'],
            '@typescript-eslint/array-type': ['error', { default: 'array' }],
            '@typescript-eslint/prefer-for-of': 'error',
            '@typescript-eslint/prefer-includes': 'error',
            '@typescript-eslint/prefer-string-starts-ends-with': 'error',
            // 通用规则
            'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
            'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
            'no-unused-vars': 'off', // 由 @typescript-eslint/no-unused-vars 处理
            'prefer-const': 'error',
            'no-var': 'error',
            'object-shorthand': 'error',
            'prefer-arrow-callback': 'error',
            'prefer-template': 'error',
            'template-curly-spacing': 'error',
            'arrow-spacing': 'error',
            'generator-star-spacing': 'error',
            'no-multiple-empty-lines': ['error', { max: 1 }],
            'no-trailing-spaces': 'error',
            'eol-last': 'error',
            'comma-dangle': ['error', 'never'],
            'quotes': ['error', 'single'],
            'semi': ['error', 'never'],
            // 导入规则
            'sort-imports': ['error', {
                    ignoreCase: false,
                    ignoreDeclarationSort: true,
                    ignoreMemberSort: false,
                    memberSyntaxSortOrder: ['none', 'all', 'multiple', 'single'],
                    allowSeparatedGroups: true
                }],
            // 代码质量规则
            'complexity': ['warn', 10],
            'max-depth': ['warn', 4],
            'max-lines': ['warn', 500],
            'max-lines-per-function': ['warn', 100],
            'max-params': ['warn', 5],
            'no-magic-numbers': ['warn', {
                    ignore: [-1, 0, 1, 2, 100, 1000],
                    ignoreArrayIndexes: true,
                    ignoreDefaultValues: true
                }]
        }
    },
    {
        files: ['**/*.vue'],
        languageOptions: {
            parser: vue.parser,
            parserOptions: {
                parser: typescriptParser,
                ecmaVersion: 2022,
                sourceType: 'module'
            }
        },
        rules: {
            '@typescript-eslint/no-unused-vars': 'off'
        }
    },
    {
        files: ['**/__tests__/**/*', '**/*.spec.*', '**/*.test.*'],
        rules: {
            '@typescript-eslint/no-explicit-any': 'off',
            'no-magic-numbers': 'off',
            'max-lines-per-function': 'off'
        }
    },
    {
        files: ['vite.config.*', 'vitest.config.*', 'playwright.config.*'],
        rules: {
            'no-console': 'off'
        }
    },
    {
        ignores: [
            'dist',
            'node_modules',
            '*.d.ts',
            'coverage',
            'public',
            '*.config.js'
        ]
    }
]);
