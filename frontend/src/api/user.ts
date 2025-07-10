import { httpClient } from './http'
import type { 
  ApiResponse, 
  UserData 
} from '@/types/api'

export interface LoginRequest {
  username: string
  password: string
  captchaToken?: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  confirmPassword: string
  captchaToken?: string
}

export interface PasswordResetRequest {
  email: string
  captchaToken?: string
}

export interface PasswordChangeRequest {
  oldPassword: string
  newPassword: string
  confirmPassword: string
}

export interface ProfileUpdateRequest {
  nickname?: string
  email?: string
  phone?: string
  avatar?: string
}

export interface TwoFactorSetupRequest {
  secret: string
  code: string
}

/**
 * 滑轨验证相关接口
 */
export interface SliderCaptchaData {
  challenge_id: string
  background_image: string
  slider_image: string
  slider_y: number
  background_width: number
  background_height: number
  expires_in: number
}

export interface SliderCaptchaResponse {
  success: boolean
  data: SliderCaptchaData | null
  message: string
  timestamp: string
}

export interface SliderVerifyRequest {
  challenge_id: string
  slider_x: number
  slider_y: number
  trail: Array<{ x: number; y: number; t: number }>
  time_cost: number
}

export interface SliderVerifyResponse {
  success: boolean
  data: { verification_token?: string } | null
  message: string
  timestamp: string
  verification_token?: string
}

// ============ 认证相关 ============

// 用户登录
export const login = async (data: LoginRequest): Promise<ApiResponse<{ user: UserData; token: string }>> => {
  const response = await httpClient.post<{ user: UserData; token: string }>('/auth/login', data)
  return response.data
}

// 用户注册
export const register = async (data: RegisterRequest): Promise<ApiResponse<UserData>> => {
  const response = await httpClient.post<UserData>('/auth/register', data)
  return response.data
}

// 用户登出
export const logout = async (): Promise<ApiResponse<void>> => {
  const response = await httpClient.post<void>('/auth/logout')
  return response.data
}

// 刷新Token
export const refreshToken = async (): Promise<ApiResponse<{ token: string }>> => {
  const response = await httpClient.post<{ token: string }>('/auth/refresh')
  return response.data
}

// 密码重置
export const resetPassword = async (data: PasswordResetRequest): Promise<ApiResponse<void>> => {
  const response = await httpClient.post<void>('/auth/reset-password', data)
  return response.data
}

// 修改密码
export const changePassword = async (data: PasswordChangeRequest): Promise<ApiResponse<void>> => {
  const response = await httpClient.post<void>('/auth/change-password', data)
  return response.data
}

// ============ 用户信息 ============

// 获取用户信息
export const getUserInfo = async (): Promise<ApiResponse<UserData>> => {
  const response = await httpClient.get<UserData>('/user/profile')
  return response.data
}

// 更新用户信息
export const updateProfile = async (data: ProfileUpdateRequest): Promise<ApiResponse<UserData>> => {
  const response = await httpClient.put<UserData>('/user/profile', data)
  return response.data
}

// 上传头像
export const uploadAvatar = async (file: File): Promise<ApiResponse<{ url: string }>> => {
  const formData = new FormData()
  formData.append('avatar', file)
  
  const response = await httpClient.post<{ url: string }>('/user/avatar', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  return response.data
}

// ============ 安全设置 ============

// 获取双因子认证设置
export const getTwoFactorStatus = async (): Promise<ApiResponse<{ enabled: boolean; secret?: string }>> => {
  const response = await httpClient.get<{ enabled: boolean; secret?: string }>('/user/2fa/status')
  return response.data
}

// 启用双因子认证
export const enableTwoFactor = async (data: TwoFactorSetupRequest): Promise<ApiResponse<void>> => {
  const response = await httpClient.post<void>('/user/2fa/enable', data)
  return response.data
}

// 禁用双因子认证
export const disableTwoFactor = async (code: string): Promise<ApiResponse<void>> => {
  const response = await httpClient.post<void>('/user/2fa/disable', { code })
  return response.data
}

// 获取登录日志
export const getLoginLogs = async (params?: { page?: number; limit?: number }): Promise<ApiResponse<any[]>> => {
  const response = await httpClient.get<any[]>('/user/login-logs', { params })
  return response.data
}

// 获取操作日志
export const getOperationLogs = async (params?: { page?: number; limit?: number }): Promise<ApiResponse<any[]>> => {
  const response = await httpClient.get<any[]>('/user/operation-logs', { params })
  return response.data
}

// ============ 偏好设置 ============

// 获取用户偏好设置
export const getPreferences = async (): Promise<ApiResponse<Record<string, any>>> => {
  const response = await httpClient.get<Record<string, any>>('/user/preferences')
  return response.data
}

// 更新用户偏好设置
export const updatePreferences = async (preferences: Record<string, any>): Promise<ApiResponse<void>> => {
  const response = await httpClient.put<void>('/user/preferences', preferences)
  return response.data
}

// ============ API密钥管理 ============

// 获取API密钥列表
export const getApiKeys = async (): Promise<ApiResponse<any[]>> => {
  const response = await httpClient.get<any[]>('/user/api-keys')
  return response.data
}

// 创建API密钥
export const createApiKey = async (data: { name: string; permissions: string[] }): Promise<ApiResponse<any>> => {
  const response = await httpClient.post<any>('/user/api-keys', data)
  return response.data
}

// 删除API密钥
export const deleteApiKey = async (keyId: string): Promise<ApiResponse<void>> => {
  const response = await httpClient.delete<void>(`/user/api-keys/${keyId}`)
  return response.data
}

// 更新API密钥权限
export const updateApiKey = async (
  keyId: string, 
  data: { name?: string; permissions?: string[] }
): Promise<ApiResponse<void>> => {
  const response = await httpClient.put<void>(`/user/api-keys/${keyId}`, data)
  return response.data
}

// ============ 通知设置 ============

// 获取通知设置
export const getNotificationSettings = async (): Promise<ApiResponse<any>> => {
  const response = await httpClient.get<any>('/user/notifications/settings')
  return response.data
}

// 更新通知设置
export const updateNotificationSettings = async (settings: any): Promise<ApiResponse<void>> => {
  const response = await httpClient.put<void>('/user/notifications/settings', settings)
  return response.data
}

// 获取通知列表
export const getNotifications = async (params?: { page?: number; limit?: number }): Promise<ApiResponse<any[]>> => {
  const response = await httpClient.get<any[]>('/user/notifications', { params })
  return response.data
}

// 标记通知为已读
export const markNotificationAsRead = async (notificationId: string): Promise<ApiResponse<void>> => {
  const response = await httpClient.put<void>(`/user/notifications/${notificationId}/read`)
  return response.data
}

// 标记所有通知为已读
export const markAllNotificationsAsRead = async (): Promise<ApiResponse<void>> => {
  const response = await httpClient.put<void>('/user/notifications/read-all')
  return response.data
}

// 删除通知
export const deleteNotification = async (notificationId: string): Promise<ApiResponse<void>> => {
  const response = await httpClient.delete<void>(`/user/notifications/${notificationId}`)
  return response.data
}

// ============ 账户管理 ============

// 获取账户统计
export const getAccountStats = async (): Promise<ApiResponse<any>> => {
  const response = await httpClient.get<any>('/user/stats')
  return response.data
}

// 注销账户
export const deleteAccount = async (password: string): Promise<ApiResponse<void>> => {
  const response = await httpClient.post<void>('/user/delete-account', { password })
  return response.data
}

// 导出用户数据
export const exportUserData = async (): Promise<void> => {
  const response = await httpClient.get('/user/export', {
    responseType: 'blob'
  })
  
  // 创建下载链接
  const blob = new Blob([response.data])
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `user-data-${Date.now()}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

export default {
  /**
   * 生成滑轨验证码
   */
  generateSliderCaptcha(): Promise<SliderCaptchaResponse> {
    return httpClient.get<SliderCaptchaResponse>('/captcha/slider')
  },

  /**
   * 验证滑轨验证码
   */
  verifySliderCaptcha(data: SliderVerifyRequest): Promise<SliderVerifyResponse> {
    return httpClient.post<SliderVerifyResponse>('/captcha/slider/verify', data)
  },

  /**
   * 验证令牌有效性
   */
  validateVerificationToken(token: string): Promise<{ success: boolean; message: string }> {
    return httpClient.post<{ success: boolean; message: string }>(`/captcha/slider/validate-token?token=${token}`, {})
  },

  /**
   * 新增：获取图片验证码
   */
  getImageCaptcha(): Promise<{ captcha_id: string; image_base64: string; captcha_text: string }> {
    return httpClient.get('/auth/captcha')
  },

  /**
   * 获取用户列表 (管理员)
   * @param params - 分页和过滤参数
   */
  getUsers(params?: Record<string, unknown>): Promise<ApiResponse<{ list: UserData[], total: number }>> {
    return httpClient.get('/users', { params })
  }
} 