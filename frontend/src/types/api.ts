// API相关类型定义

import { BaseResponse, ListResponse } from './common'

// HTTP方法类型
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'

// 请求配置
export interface RequestConfig {
  url: string
  method?: HttpMethod
  params?: Record<string, any>
  data?: any
  headers?: Record<string, string>
  timeout?: number
  withCredentials?: boolean
}

// 响应类型
export interface ApiSuccessResponse<T = any> extends BaseResponse<T> {
  code: 200
  success: true
}

export interface ApiErrorResponse extends BaseResponse<null> {
  code: number
  success: false
  error: {
    type: string
    message: string
    details?: any
  }
}

export type ApiResponse<T = any> = ApiSuccessResponse<T> | ApiErrorResponse

// 分页请求参数
export interface PaginationRequest {
  page?: number
  pageSize?: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

// 列表响应
export interface ListApiResponse<T> extends ApiSuccessResponse<ListResponse<T>> {}

// 认证相关
export interface LoginRequest {
  username: string
  password: string
  captcha?: string
  rememberMe?: boolean
}

export interface LoginResponse {
  token: string
  refreshToken: string
  expiresIn: number
  user: {
    id: string
    username: string
    email: string
    avatar?: string
    roles: string[]
    permissions: string[]
  }
}

export interface RefreshTokenRequest {
  refreshToken: string
}

export interface RefreshTokenResponse {
  token: string
  expiresIn: number
}

// 文件上传
export interface UploadRequest {
  file: File
  filename?: string
  category?: string
}

export interface UploadResponse {
  url: string
  filename: string
  size: number
  mimeType: string
  hash: string
}

// WebSocket消息类型
export interface WSMessage<T = any> {
  type: string
  data: T
  timestamp: number
  id?: string
}

export interface WSSubscribeMessage {
  action: 'subscribe' | 'unsubscribe'
  channel: string
  params?: Record<string, any>
}

export interface WSHeartbeatMessage {
  type: 'ping' | 'pong'
  timestamp: number
}

// API错误类型
export interface ApiError {
  code: string
  message: string
  field?: string
  details?: any
}

export interface ValidationError {
  field: string
  message: string
  value?: any
}

// 搜索请求
export interface SearchRequest extends PaginationRequest {
  keyword?: string
  filters?: Record<string, any>
  dateRange?: {
    start: string
    end: string
  }
}

// 批量操作
export interface BatchRequest<T = any> {
  action: string
  items: T[]
  options?: Record<string, any>
}

export interface BatchResponse<T = any> {
  success: T[]
  failed: Array<{
    item: T
    error: ApiError
  }>
  total: number
  successCount: number
  failedCount: number
} 