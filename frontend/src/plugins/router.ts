/**
 * Vue Router 配置
 */
import type { App } from 'vue'
import router from '@/router'

export const setupRouter = (app: App) => {
  app.use(router)
  return router
}