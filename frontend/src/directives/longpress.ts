/**
 * 长按指令
 * v-longpress:500="handler"
 */
import type { Directive } from 'vue'

interface LongpressElement extends HTMLElement {
  _longpressTimer?: NodeJS.Timeout
  _longpressStartHandler?: EventListener
  _longpressEndHandler?: EventListener
}

export const longpress: Directive = {
  mounted(el: LongpressElement, binding) {
    const duration = parseInt(binding.arg || '500')
    
    const startHandler = () => {
      el._longpressTimer = setTimeout(() => {
        if (typeof binding.value === 'function') {
          binding.value()
        }
      }, duration)
    }
    
    const endHandler = () => {
      if (el._longpressTimer) {
        clearTimeout(el._longpressTimer)
        delete el._longpressTimer
      }
    }
    
    el._longpressStartHandler = startHandler
    el._longpressEndHandler = endHandler
    
    el.addEventListener('mousedown', startHandler)
    el.addEventListener('mouseup', endHandler)
    el.addEventListener('mouseleave', endHandler)
    el.addEventListener('touchstart', startHandler)
    el.addEventListener('touchend', endHandler)
  },
  
  unmounted(el: LongpressElement) {
    if (el._longpressTimer) {
      clearTimeout(el._longpressTimer)
    }
    
    if (el._longpressStartHandler) {
      el.removeEventListener('mousedown', el._longpressStartHandler)
      el.removeEventListener('touchstart', el._longpressStartHandler)
      delete el._longpressStartHandler
    }
    
    if (el._longpressEndHandler) {
      el.removeEventListener('mouseup', el._longpressEndHandler)
      el.removeEventListener('mouseleave', el._longpressEndHandler)
      el.removeEventListener('touchend', el._longpressEndHandler)
      delete el._longpressEndHandler
    }
  }
}