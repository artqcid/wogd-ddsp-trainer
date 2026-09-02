import pluginVue from 'eslint-plugin-vue'

export default [
  // Vue recommended rules (includes vue/no-parsing-error, vue/html-end-tags, etc.)
  ...pluginVue.configs['flat/recommended'],

  // Project-specific overrides
  {
    files: ['src/**/*.vue'],
    rules: {
      // Enforce every opened HTML tag is properly closed — catches stray </div> class of bugs
      'vue/html-end-tags': 'error',
      // Catch any template parse errors (unclosed tags, invalid nesting)
      'vue/no-parsing-error': 'error',
      // Downgrade style-only rules that add noise without catching real bugs
      'vue/max-attributes-per-line': 'off',
      'vue/singleline-html-element-content-newline': 'off',
      'vue/multiline-html-element-content-newline': 'off',
      'vue/html-self-closing': 'off',
      'vue/html-indent': 'off',
      'vue/attributes-order': 'off',
      'vue/component-tags-order': 'off',
      'vue/order-in-components': 'off',
    },
  },

  {
    files: ['src/**/*.js'],
    rules: {},
  },

  {
    // Ignore build output and dependencies
    ignores: ['dist/**', 'node_modules/**'],
  },
]
