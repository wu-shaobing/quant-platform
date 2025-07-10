/**
 * 加载指令
 * v-loading="isLoading"
 */
import type { Directive } from 'vue'

interface LoadingElement extends HTMLElement {
  _loadingInstance?: {
    el: HTMLElement
    visible: boolean
  }
}

const createLoadingElement = (): HTMLElement => {
  const loadingEl = document.createElement('div')
  loadingEl.className = 'v-loading-mask'
  loadingEl.innerHTML = `
    <div class="v-loading-spinner">
      <svg class="circular" viewBox="25 25 50 50">
        <circle class="path" cx="50" cy="50" r="20" fill="none" stroke="currentColor" stroke-width="2" stroke-miterlimit="10"/>
      </svg>
      <p class="v-loading-text">加载中...</p>
    </div>
  `
  
  return loadingEl
}

export const loading: Directive = {
  mounted(el: LoadingElement, binding) {
    if (binding.value) {
      const loadingEl = createLoadingElement()
      const position = getComputedStyle(el).position
      if (position === 'static') {
        el.style.position = 'relative'
      }
      el.appendChild(loadingEl)
      el._loadingInstance = { el: loadingEl, visible: true }
    }
  },
  
  updated(el: LoadingElement, binding) {
    if (binding.value !== binding.oldValue) {
      if (binding.value && !el._loadingInstance?.visible) {
        const loadingEl = createLoadingElement()
        el.appendChild(loadingEl)
        el._loadingInstance = { el: loadingEl, visible: true }
      } else if (!binding.value && el._loadingInstance?.visible) {
        const loadingEl = el._loadingInstance.el
        if (loadingEl?.parentNode) {
          loadingEl.parentNode.removeChild(loadingEl)
        }
        el._loadingInstance.visible = false
      }
    }
  }
}