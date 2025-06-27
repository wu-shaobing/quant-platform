import type { ButtonProps as ElButtonProps } from 'element-plus'

// 按钮尺寸类型
export type ButtonSize = 'large' | 'default' | 'small'

// 按钮类型
export type ButtonType = 
  | 'primary' 
  | 'success' 
  | 'warning' 
  | 'danger' 
  | 'info' 
  | 'text'

// 按钮变体
export type ButtonVariant = 'solid' | 'outline' | 'ghost' | 'link'

// 扩展的按钮属性
export interface AppButtonProps extends Partial<ElButtonProps> {
  variant?: ButtonVariant
  loading?: boolean
  disabled?: boolean
  icon?: string
  iconPosition?: 'left' | 'right'
  block?: boolean
  shape?: 'default' | 'round' | 'circle'
  htmlType?: 'button' | 'submit' | 'reset'
}

// 按钮事件
export interface AppButtonEmits {
  click: [event: MouseEvent]
  focus: [event: FocusEvent]
  blur: [event: FocusEvent]
}
