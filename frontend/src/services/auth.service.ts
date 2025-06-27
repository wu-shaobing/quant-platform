import { http } from '@/api/http'
import { jwtDecode } from 'jwt-decode'
import type { LoginData, LoginResponse, UserInfo, RefreshTokenResponse, LoginCredentials, RegisterCredentials, User } from '@/types/user'

export interface AuthResponse {
  user: User
  token: string
  refreshToken?: string
}

/**
 * 认证服务类 - 单例模式
 */
class AuthService {
  private static instance: AuthService
  private tokenKey = 'quant_auth_token'
  private refreshTokenKey = 'quant_refresh_token'
  private userInfoKey = 'quant_user_info'
  private refreshTimer: NodeJS.Timeout | null = null

  private constructor() {
    this.initTokenRefresh()
  }

  /**
   * 获取单例实例
   */
  public static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService()
    }
    return AuthService.instance
  }

  /**
   * 用户登录
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await http.post<AuthResponse>('/auth/login', credentials)
    return response.data
  }

  /**
   * 用户注册
   */
  async register(credentials: RegisterCredentials): Promise<AuthResponse> {
    const response = await http.post<AuthResponse>('/auth/register', credentials)
    return response.data
  }

  /**
   * 用户登出
   */
  async logout(): Promise<void> {
    await http.post('/auth/logout')
  }

  /**
   * 刷新token
   */
  async refreshToken(): Promise<{ token: string }> {
    const response = await http.post<{ token: string }>('/auth/refresh')
    return response.data
  }

  /**
   * 获取用户信息
   */
  async getUserProfile(): Promise<User> {
    const response = await http.get<User>('/auth/profile')
    return response.data
  }

  /**
   * 更新用户信息
   */
  async updateProfile(profileData: Partial<User>): Promise<User> {
    const response = await http.put<User>('/auth/profile', profileData)
    return response.data
  }

  /**
   * 修改密码
   */
  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await http.post('/auth/change-password', {
      oldPassword,
      newPassword
    })
  }

  /**
   * 发送重置密码验证码
   */
  async sendResetCode(email: string): Promise<void> {
    await http.post('/auth/send-reset-code', { email })
  }

  /**
   * 重置密码
   */
  async resetPassword(data: {
    email: string
    code: string
    newPassword: string
  }): Promise<void> {
    await http.post('/auth/reset-password', data)
  }

  /**
   * 验证token有效性
   */
  async validateToken(): Promise<boolean> {
    try {
      await http.get('/auth/validate')
      return true
    } catch {
      return false
    }
  }

  /**
   * 获取当前用户信息
   */
  async getCurrentUser(): Promise<UserInfo> {
    try {
      const response = await http.get<{ data: UserInfo }>('/auth/me')

      if (response.data) {
        this.setUserInfo(response.data)
        return response.data
      } else {
        throw new Error('获取用户信息失败')
      }
    } catch (error) {
      console.error('获取用户信息失败:', error)
      throw error
    }
  }

  /**
   * 验证重置密码token
   */
  async verifyResetToken(token: string): Promise<boolean> {
    try {
      const response = await http.post('/auth/verify-reset-token', { token })
      return response.success
    } catch (error) {
      console.error('验证重置token失败:', error)
      return false
    }
  }

  /**
   * 确认重置密码
   */
  async confirmResetPassword(data: {
    token: string
    newPassword: string
    confirmPassword: string
  }): Promise<void> {
    try {
      const response = await http.post('/auth/confirm-reset-password', data)

      if (!response.success) {
        throw new Error(response.message || '重置密码失败')
      }
    } catch (error) {
      console.error('确认重置密码失败:', error)
      throw error
    }
  }

  /**
   * 获取token
   */
  getToken(): string | null {
    return localStorage.getItem(this.tokenKey)
  }

  /**
   * 设置token
   */
  setToken(token: string): void {
    localStorage.setItem(this.tokenKey, token)
  }

  /**
   * 获取刷新token
   */
  getRefreshToken(): string | null {
    return localStorage.getItem(this.refreshTokenKey)
  }

  /**
   * 设置刷新token
   */
  setRefreshToken(token: string): void {
    localStorage.setItem(this.refreshTokenKey, token)
  }

  /**
   * 获取用户信息
   */
  getUserInfo(): UserInfo | null {
    const userInfo = localStorage.getItem(this.userInfoKey)
    return userInfo ? JSON.parse(userInfo) : null
  }

  /**
   * 设置用户信息
   */
  setUserInfo(userInfo: UserInfo): void {
    localStorage.setItem(this.userInfoKey, JSON.stringify(userInfo))
  }

  /**
   * 检查用户是否已认证
   */
  isAuthenticated(): boolean {
    const token = this.getToken()
    if (!token) return false

    try {
      const decoded = jwtDecode(token)
      const currentTime = Date.now() / 1000

      // 检查token是否过期
      if (decoded.exp && decoded.exp < currentTime) {
        return false
      }

      return true
    } catch (error) {
      console.error('Token解析失败:', error)
      return false
    }
  }

  /**
   * 检查token是否即将过期
   */
  isTokenExpiringSoon(): boolean {
    const token = this.getToken()
    if (!token) return false

    try {
      const decoded = jwtDecode(token)
      const currentTime = Date.now() / 1000
      const expirationTime = decoded.exp || 0

      // 如果token在5分钟内过期，认为即将过期
      return expirationTime - currentTime < 300
    } catch (error) {
      console.error('Token解析失败:', error)
      return true
    }
  }

  /**
   * 获取token过期时间
   */
  getTokenExpiration(): Date | null {
    const token = this.getToken()
    if (!token) return null

    try {
      const decoded = jwtDecode(token)
      return decoded.exp ? new Date(decoded.exp * 1000) : null
    } catch (error) {
      console.error('Token解析失败:', error)
      return null
    }
  }

  /**
   * 清除认证信息
   */
  clearAuth(): void {
    localStorage.removeItem(this.tokenKey)
    localStorage.removeItem(this.refreshTokenKey)
    localStorage.removeItem(this.userInfoKey)
  }

  /**
   * 初始化token刷新
   */
  private initTokenRefresh(): void {
    // 页面加载时检查token状态
    if (this.isAuthenticated() && this.isTokenExpiringSoon()) {
      this.refreshToken().catch(() => {
        // 刷新失败，清除认证信息
        this.clearAuth()
      })
    } else if (this.isAuthenticated()) {
      this.startTokenRefresh()
    }
  }

  /**
   * 启动token刷新定时器
   */
  private startTokenRefresh(): void {
    this.stopTokenRefresh()

    const token = this.getToken()
    if (!token) return

    try {
      const decoded = jwtDecode(token)
      const currentTime = Date.now() / 1000
      const expirationTime = decoded.exp || 0

      // 在token过期前5分钟刷新
      const refreshTime = (expirationTime - currentTime - 300) * 1000

      if (refreshTime > 0) {
        this.refreshTimer = setTimeout(() => {
          this.refreshToken().catch(() => {
            // 刷新失败，清除认证信息
            this.clearAuth()
          })
        }, refreshTime)
      }
    } catch (error) {
      console.error('启动token刷新定时器失败:', error)
    }
  }

  /**
   * 停止token刷新定时器
   */
  private stopTokenRefresh(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer)
      this.refreshTimer = null
    }
  }

  /**
   * 检查用户权限
   */
  hasPermission(permission: string): boolean {
    const userInfo = this.getUserInfo()
    if (!userInfo || !userInfo.permissions) return false

    return userInfo.permissions.includes(permission)
  }

  /**
   * 检查用户角色
   */
  hasRole(role: string): boolean {
    const userInfo = this.getUserInfo()
    if (!userInfo || !userInfo.roles) return false

    return userInfo.roles.includes(role)
  }

  /**
   * 检查是否为VIP用户
   */
  isVipUser(): boolean {
    const userInfo = this.getUserInfo()
    return userInfo?.isVip || false
  }

  /**
   * 获取用户等级
   */
  getUserLevel(): string {
    const userInfo = this.getUserInfo()
    return userInfo?.level || 'basic'
  }
}

// 导出单例实例
export const authService = AuthService.getInstance()
export default authService
