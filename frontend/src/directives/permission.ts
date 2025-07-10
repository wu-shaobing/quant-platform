/**
 * 权限指令
 * v-permission="'admin'"
 * v-permission="['admin', 'user']"
 */
import type { Directive } from 'vue'
import { useUserStore } from '@/stores/modules/user'

export const permission: Directive = {
  mounted(el: HTMLElement, binding) {
    const userStore = useUserStore()
    const requiredPermissions = Array.isArray(binding.value) 
      ? binding.value 
      : [binding.value]
    
    const hasPermission = requiredPermissions.some(permission => 
      userStore.hasPermission && userStore.hasPermission(permission)
    )
    
    if (!hasPermission) {
      el.style.display = 'none'
    }
  },
  
  updated(el: HTMLElement, binding) {
    const userStore = useUserStore()
    const requiredPermissions = Array.isArray(binding.value) 
      ? binding.value 
      : [binding.value]
    
    const hasPermission = requiredPermissions.some(permission => 
      userStore.hasPermission && userStore.hasPermission(permission)
    )
    
    el.style.display = hasPermission ? '' : 'none'
  }
}