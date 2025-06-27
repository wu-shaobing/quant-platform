import { http } from './http'
import type { User, LoginCredentials, RegisterData, UserProfile } from '@/types/user'
import type { ApiResponse } from '@/types'

const BASE_URL = '/user'

/**
 * 用户认证和管理API
 */
export const userApi = {
  /**
   * 用户登录
   * @param credentials - 登录凭据 (username, password)
   */
  login(credentials: LoginCredentials): Promise<{ accessToken: string, refreshToken: string }> {
    return http.post(`${BASE_URL}/login`, credentials)
  },

  /**
   * 用户注册
   * @param data - 注册信息
   */
  register(data: RegisterData): Promise<User> {
    return http.post(`${BASE_URL}/register`, data)
  },

  /**
   * 刷新Token
   * @param refreshToken - 刷新令牌
   */
  refreshToken(refreshToken: string): Promise<{ token: string }> {
    return http.post('/auth/refresh', { refreshToken })
  },
  
  /**
   * 用户登出
   */
  logout(): Promise<void> {
    return http.post(`${BASE_URL}/logout`)
  },

  /**
   * 获取当前登录用户信息
   */
  getCurrentUser(): Promise<User> {
    return http.get(`${BASE_URL}/me`)
  },

  /**
   * 获取用户信息（同getCurrentUser，为了兼容性）
   */
  getUserInfo(): Promise<User> {
    return this.getCurrentUser()
  },
  
  /**
   * 更新用户个人资料
   * @param profile - 用户资料
   */
  updateProfile(profile: Partial<UserProfile>): Promise<User> {
    return http.put(`${BASE_URL}/profile`, profile)
  },

  /**
   * 修改密码
   * @param data - { oldPassword, newPassword }
   */
  changePassword(data: { oldPassword: string; newPassword: string }): Promise<void> {
    return http.post(`${BASE_URL}/change-password`, data)
  },

  /**
   * 发送重置密码验证码
   * @param email - 邮箱地址
   */
  sendResetCode(email: string): Promise<void> {
    return http.post(`${BASE_URL}/send-reset-code`, { email })
  },

  /**
   * 重置密码
   * @param data - { email, code }
   */
  resetPassword(data: { email: string; code: string }): Promise<void> {
    return http.post(`${BASE_URL}/reset-password`, data)
  },

  /**
   * 获取用户列表 (管理员)
   * @param params - 分页和过滤参数
   */
  getUsers(params?: Record<string, unknown>): Promise<ApiResponse<{ list: User[], total: number }>> {
    return http.get(`${BASE_URL}/list`, { params })
  }
}

export default userApi 