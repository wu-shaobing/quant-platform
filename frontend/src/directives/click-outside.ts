/**
 * 点击外部指令
 * v-click-outside="handler"
 */
import type { Directive } from 'vue'

interface ClickOutsideElement extends HTMLElement {
  _clickOutsideHandler?: (event: Event) => void
}

export const clickOutside: Directive = {
  mounted(el: ClickOutsideElement, binding) {
    const handler = (event: Event) => {
      if (el.contains(event.target as Node)) {
        return
      }
      
      if (typeof binding.value === 'function') {
        binding.value(event)
      }
    }
    
    el._clickOutsideHandler = handler
    document.addEventListener('click', handler, true)
  },
  
  unmounted(el: ClickOutsideElement) {
    if (el._clickOutsideHandler) {
      document.removeEventListener('click', el._clickOutsideHandler, true)
      delete el._clickOutsideHandler
    }
  }
}