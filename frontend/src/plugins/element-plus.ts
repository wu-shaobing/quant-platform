/**
 * Element Plus 配置
 */
import type { App } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import en from 'element-plus/es/locale/lang/en'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

export const setupElementPlus = (app: App) => {
  // 安装 Element Plus
  app.use(ElementPlus, {
    locale: zhCn,
    size: 'default'
  })
  
  // 注册所有图标
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }
}

// 语言配置
export const locales = {
  'zh-cn': zhCn,
  'en': en
}