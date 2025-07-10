import { createI18n } from 'vue-i18n'
import zhCN from './zh-CN'
import enUS from './en-US'

// 支持的语言列表
export const supportedLocales = [
  {
    code: 'zh-CN',
    name: '简体中文',
    flag: '🇨🇳'
  },
  {
    code: 'en-US', 
    name: 'English',
    flag: '🇺🇸'
  }
] as const

export type SupportedLocale = typeof supportedLocales[number]['code']

// 获取默认语言
const getDefaultLocale = (): SupportedLocale => {
  // 优先从localStorage获取
  const stored = localStorage.getItem('locale')
  if (stored && supportedLocales.some(locale => locale.code === stored)) {
    return stored as SupportedLocale
  }
  
  // 其次从浏览器语言获取
  const browserLang = navigator.language
  if (browserLang.startsWith('zh')) {
    return 'zh-CN'
  }
  
  // 默认英文
  return 'en-US'
}

// 创建i18n实例
export const i18n = createI18n({
  legacy: false,
  locale: getDefaultLocale(),
  fallbackLocale: 'en-US',
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS
  },
  globalInjection: true,
  warnHtmlMessage: false
})

// 设置语言
export const setLocale = (locale: SupportedLocale) => {
  i18n.global.locale.value = locale
  localStorage.setItem('locale', locale)
  document.documentElement.lang = locale
}

// 获取当前语言
export const getCurrentLocale = (): SupportedLocale => {
  return i18n.global.locale.value as SupportedLocale
}

// 切换语言
export const toggleLocale = () => {
  const current = getCurrentLocale()
  const newLocale = current === 'zh-CN' ? 'en-US' : 'zh-CN'
  setLocale(newLocale)
}

// 获取语言显示名称
export const getLocaleName = (locale: SupportedLocale): string => {
  const found = supportedLocales.find(item => item.code === locale)
  return found?.name || locale
}

export default i18n 