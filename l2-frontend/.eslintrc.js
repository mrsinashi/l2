module.exports = {
  root: true,
  env: {
    node: true,
  },
  extends: [
    'plugin:vue/essential',
    'plugin:vue/recommended',
    'plugin:vue/strongly-recommended',
    '@vue/airbnb',
    '@vue/typescript/recommended',
  ],
  plugins: [
    'sort-imports-es6-autofix',
  ],
  parserOptions: {
    ecmaVersion: 2020,
  },
  rules: {
    'no-console': process.env.NODE_ENV === 'production' ? 'error' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'off',
    '@typescript-eslint/ban-ts-comment': 'off',
    'no-plusplus': 'off',
    'no-restricted-syntax': ['error', 'ForInStatement', 'LabeledStatement', 'WithStatement'],
    'no-continue': 'off',
    'no-await-in-loop': 'off',
    'max-len': ['error', { code: 130 }],
    camelcase: 'error',
    'arrow-parens': 'off',
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/no-explicit-any': 'off',
    'func-names': 'off',
    'vue/prop-name-casing': 'off',
    'vue/multi-word-component-names': 'off',
    'vue/require-default-prop': 'off',
    'vue/require-prop-types': 'off',
    'vue/no-use-v-if-with-v-for': 'off',
    'vue/component-name-in-template-casing': ['error', 'PascalCase'],
    'vue/order-in-components': 'error',
    'vue/padding-line-between-blocks': 'error',
    '@typescript-eslint/prefer-optional-chain': 'error',
    'vuejs-accessibility/label-has-for': 'off',
    'vuejs-accessibility/form-control-has-label': 'off',
    'vuejs-accessibility/click-events-have-key-events': 'off',
    'vuejs-accessibility/mouse-events-have-key-events': 'off',
    'vuejs-accessibility/anchor-has-content': 'off',
    'vuejs-accessibility/iframe-has-title': 'off',
    'vuejs-accessibility/no-autofocus': 'off',
    'vuejs-accessibility/alt-text': 'off',
    'vuejs-accessibility/media-has-caption': 'off',
    'import/order': [
      'error',
      {
        groups: [
          ['builtin', 'external'],
          'internal',
          ['parent', 'sibling', 'index'],
        ],
        'newlines-between': 'always',
      },
    ],
    'sort-imports': [
      'error',
      {
        ignoreDeclarationSort: true,
        ignoreCase: true,
        ignoreMemberSort: false,
      },
    ],
  },
  overrides: [
    {
      files: ['*.ts', '*.tsx'],
      rules: {
        '@typescript-eslint/explicit-module-boundary-types': ['off'],
      },
    },
  ],
};
