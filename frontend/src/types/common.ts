// 通用类型定义

export interface BaseResponse<T = any> {
  code: number
  data: T
  message: string
  timestamp: number
}

export interface ErrorResponse {
  code: number
  message: string
  timestamp: number
  details?: any
}

export interface ListResponse<T> {
  list: T[]
  total: number
  page: number
  pageSize: number
  hasNext: boolean
}

export interface SelectOption {
  label: string
  value: string | number
  disabled?: boolean
  children?: SelectOption[]
}

export interface TableColumn {
  key: string
  title: string
  width?: number
  align?: 'left' | 'center' | 'right'
  sortable?: boolean
  filterable?: boolean
  render?: (value: any, record: any) => any
}

export interface SortParams {
  field: string
  order: 'asc' | 'desc'
}

export interface FilterParams {
  field: string
  operator: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'like' | 'in'
  value: any
}

export type LoadingState = 'idle' | 'loading' | 'success' | 'error'

export interface AsyncState<T = any> {
  data: T | null
  loading: boolean
  error: string | null
  lastUpdated: number | null
}

export type ComponentSize = 'small' | 'default' | 'large'
export type ComponentType = 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default'

export interface BaseConfig {
  id: string
  name: string
  description?: string
  enabled: boolean
  createdAt: string
  updatedAt: string
} 