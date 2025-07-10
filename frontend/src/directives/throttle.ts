/**
 * 节流指令
 * v-throttle:1000="handler"
 */
import type { Directive } from 'vue'

interface ThrottleElement extends HTMLElement {
  _throttleHandler?: EventListener
  _lastExecTime?: number
}

export const throttle: Directive = {
  mounted(el: ThrottleElement, binding) {
    const delay = parseInt(binding.arg || '1000')
    
    const handler = (e: Event) => {
      const now = Date.now()
      
      if (!el._lastExecTime || now - el._lastExecTime >= delay) {
        el._lastExecTime = now
        if (typeof binding.value === 'function') {
          binding.value(e)
        }
      }
    }
    
    el._throttleHandler = handler
    el.addEventListener('click', handler)
  },
  
  unmounted(el: ThrottleElement) {
    if (el._throttleHandler) {
      el.removeEventListener('click', el._throttleHandler)
      delete el._throttleHandler
    }
  }
}