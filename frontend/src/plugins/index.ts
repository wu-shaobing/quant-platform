/**
 * 插件统一管理
 */
import type { App } from 'vue'
import { setupElementPlus } from './element-plus'
import { setupECharts } from './echarts'
import { setupPinia } from './pinia'
import { setupRouter } from './router'
import { setupI18n } from './i18n'
import { setupDirectives } from '@directives/index'

export const setupPlugins = (app: App) => {
  // 状态管理
  setupPinia(app)
  
  // 路由
  setupRouter(app)
  
  // UI组件库
  setupElementPlus(app)
  
  // 图表库
  setupECharts()
  
  // 国际化
  setupI18n(app)

  // 自定义指令
  setupDirectives(app)
}