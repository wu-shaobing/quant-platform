/**
 * Pinia 状态管理配置
 */
import type { App } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

export const setupPinia = (app: App) => {
  const pinia = createPinia()
  
  // 持久化插件
  pinia.use(piniaPluginPersistedstate)
  
  app.use(pinia)
  
  return pinia
}