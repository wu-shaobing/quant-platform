/**
 * 复制指令
 * v-copy="text"
 */
import type { Directive } from 'vue'
import { ElMessage } from 'element-plus'

export const copy: Directive = {
  mounted(el: HTMLElement, binding) {
    el.addEventListener('click', async () => {
      const text = binding.value
      
      if (!text) {
        ElMessage.warning('没有可复制的内容')
        return
      }
      
      try {
        if (navigator.clipboard) {
          await navigator.clipboard.writeText(text)
        } else {
          const textarea = document.createElement('textarea')
          textarea.value = text
          textarea.style.position = 'fixed'
          textarea.style.left = '-9999px'
          document.body.appendChild(textarea)
          textarea.select()
          document.execCommand('copy')
          document.body.removeChild(textarea)
        }
        
        ElMessage.success('复制成功')
      } catch (error) {
        console.error('复制失败:', error)
        ElMessage.error('复制失败')
      }
    })
  }
}