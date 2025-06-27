/**
 * 防抖指令
 * v-debounce:300="handler"
 */
import type { Directive } from 'vue'

interface DebounceElement extends HTMLElement {
  _debounceTimer?: NodeJS.Timeout
  _debounceHandler?: EventListener
}

export const debounce: Directive = {
  mounted(el: DebounceElement, binding) {
    const delay = parseInt(binding.arg || '300')
    
    const handler = (e: Event) => {
      if (el._debounceTimer) {
        clearTimeout(el._debounceTimer)
      }
      
      el._debounceTimer = setTimeout(() => {
        if (typeof binding.value === 'function') {
          binding.value(e)
        }
      }, delay)
    }
    
    el._debounceHandler = handler
    el.addEventListener('click', handler)
  },
  
  unmounted(el: DebounceElement) {
    if (el._debounceTimer) {
      clearTimeout(el._debounceTimer)
    }
    
    if (el._debounceHandler) {
      el.removeEventListener('click', el._debounceHandler)
      delete el._debounceHandler
    }
  }
}