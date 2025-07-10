module.exports = {
  extends: [
    'stylelint-config-standard',
    'stylelint-config-standard-scss',
    'stylelint-config-standard-vue'
  ],
  plugins: [
    'stylelint-order'
  ],
  rules: {
    // 基础规则
    'string-quotes': 'single',
    'color-hex-case': 'lower',
    'color-hex-length': 'short',
    'selector-class-pattern': null,
    'selector-id-pattern': null,
    'keyframes-name-pattern': null,
    'custom-property-pattern': null,
    'no-descending-specificity': null,
    'declaration-empty-line-before': null,

    // SCSS 规则
    'scss/at-rule-no-unknown': [true, {
      ignoreAtRules: [
        'tailwind',
        'apply',
        'variants',
        'responsive',
        'screen',
        'layer'
      ]
    }],
    'scss/dollar-variable-pattern': '^[a-z][a-zA-Z0-9-]*$',
    'scss/at-mixin-pattern': '^[a-z][a-zA-Z0-9-]*$',
    'scss/at-function-pattern': '^[a-z][a-zA-Z0-9-]*$',

    // 属性顺序
    'order/properties-order': [
      // 定位
      'position',
      'top',
      'right',
      'bottom',
      'left',
      'z-index',

      // 显示模式
      'display',
      'flex',
      'flex-grow',
      'flex-shrink',
      'flex-basis',
      'flex-direction',
      'flex-wrap',
      'justify-content',
      'align-items',
      'align-content',
      'align-self',
      'order',
      'grid',
      'grid-area',
      'grid-template',
      'grid-template-areas',
      'grid-template-rows',
      'grid-template-columns',
      'grid-row',
      'grid-column',
      'grid-row-start',
      'grid-row-end',
      'grid-column-start',
      'grid-column-end',
      'grid-auto-rows',
      'grid-auto-columns',
      'grid-auto-flow',
      'grid-gap',
      'grid-row-gap',
      'grid-column-gap',

      // 盒模型
      'width',
      'height',
      'max-width',
      'max-height',
      'min-width',
      'min-height',
      'padding',
      'padding-top',
      'padding-right',
      'padding-bottom',
      'padding-left',
      'margin',
      'margin-top',
      'margin-right',
      'margin-bottom',
      'margin-left',
      'overflow',
      'overflow-x',
      'overflow-y',

      // 边框
      'border',
      'border-width',
      'border-style',
      'border-color',
      'border-top',
      'border-right',
      'border-bottom',
      'border-left',
      'border-radius',

      // 背景
      'background',
      'background-color',
      'background-image',
      'background-repeat',
      'background-attachment',
      'background-position',
      'background-size',
      'background-clip',
      'background-origin',

      // 文字
      'color',
      'font',
      'font-weight',
      'font-size',
      'font-family',
      'font-style',
      'font-variant',
      'font-size-adjust',
      'font-stretch',
      'font-effect',
      'font-emphasize',
      'font-emphasize-position',
      'font-emphasize-style',
      'font-smooth',
      'line-height',
      'direction',
      'letter-spacing',
      'white-space',
      'text-align',
      'text-align-last',
      'text-decoration',
      'text-emphasis',
      'text-emphasis-color',
      'text-emphasis-style',
      'text-emphasis-position',
      'text-indent',
      'text-justify',
      'text-outline',
      'text-transform',
      'text-wrap',
      'text-overflow',
      'text-overflow-ellipsis',
      'text-overflow-mode',
      'text-shadow',
      'word-spacing',
      'word-wrap',
      'word-break',

      // 其他
      'opacity',
      'visibility',
      'box-shadow',
      'text-shadow',
      'transform',
      'transition',
      'animation'
    ]
  },
  ignoreFiles: [
    'dist/**/*',
    'node_modules/**/*',
    'coverage/**/*'
  ]
} 