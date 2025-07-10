/**
 * 全局指令注册
 */
import type { App } from 'vue'
import { loading } from './loading'
import { clickOutside } from './click-outside'
import { copy } from './copy'
import { debounce } from './debounce'
import { throttle } from './throttle'
import { permission } from './permission'
import { longpress } from './longpress'

export function setupDirectives(app: App) {
  app.directive('loading', loading)
  app.directive('click-outside', clickOutside)
  app.directive('copy', copy)
  app.directive('debounce', debounce)
  app.directive('throttle', throttle)
  app.directive('permission', permission)
  app.directive('longpress', longpress)
}

export {
  loading,
  clickOutside,
  copy,
  debounce,
  throttle,
  permission,
  longpress
}