// Element Plus 组件类型声明
import type { VNode } from 'vue'

// 消息类型 - 支持字符串和对象参数
export type MessageParamsWithType = string | {
  message?: string | VNode
  type?: 'success' | 'warning' | 'info' | 'error'
  duration?: number
  showClose?: boolean
  center?: boolean
  onClose?: () => void
}

// 表单相关类型
export type FormItemProp = string | string[]

export interface FormItemRule {
  required?: boolean
  message?: string
  trigger?: string | string[]
  min?: number
  max?: number
  len?: number
  pattern?: RegExp
  validator?: (rule: any, value: any, callback: (error?: Error) => void) => void
  type?: string
}

export type FormRules = Partial<Record<string, FormItemRule | FormItemRule[]>>

// 自动完成数据类型
export interface AutocompleteData {
  value: string
  label?: string
  [key: string]: any
}

// 复选框值类型
export type CheckboxValueType = string | number | boolean

declare global {
  // Element Plus 全局组件类型
  interface GlobalComponents {
    ElButton: any
    ElTabs: any
    ElTabPane: any
    ElTag: any
    ElRadioGroup: any
    ElDialog: any
    ElDatePicker: any
    ElCheckbox: any
    ElSelect: any
    ElOption: any
    ElAutocomplete: any
    ElRadio: any
    ElForm: any
    ElFormItem: any
    ElInput: any
    ElInputNumber: any
    ElCard: any
    ElIcon: any
  }
}

// 模块声明，覆盖 Element Plus 的消息类型
declare module 'element-plus' {
  interface ElMessage {
    (message: string): void
    (options: {
      message?: string | VNode
      type?: 'success' | 'warning' | 'info' | 'error'
      duration?: number
      showClose?: boolean
      center?: boolean
      onClose?: () => void
    }): void
    success(message: string): void
    warning(message: string): void
    info(message: string): void
    error(message: string): void
  }
} 