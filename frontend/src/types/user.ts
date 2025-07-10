/**
 * 用户相关类型定义
 */

// 用户状态
export type UserStatus = 'active' | 'inactive' | 'suspended' | 'pending'

// 用户角色
export type UserRole = 'admin' | 'user' | 'vip' | 'guest'

// 用户基础信息
export interface User {
  id: string
  username: string
  email: string
  phone?: string
  avatar?: string
  nickname?: string
  realName?: string

  // 状态信息
  status: UserStatus
  role: UserRole
  isEmailVerified: boolean
  isPhoneVerified: boolean
  isVip?: boolean

  // 时间信息
  createdAt: string
  updatedAt: string
  lastLoginAt?: string

  // 个人信息
  profile?: UserProfile

  // 偏好设置
  preferences?: UserPreferences

  // 权限信息
  permissions?: string[]
}

// 用户详细信息
export interface UserProfile {
  // 基本信息
  firstName?: string
  lastName?: string
  gender?: 'male' | 'female' | 'other'
  birthday?: string
  country?: string
  city?: string
  timezone?: string

  // 联系信息
  address?: string
  website?: string

  // 职业信息
  occupation?: string
  company?: string
  industry?: string

  // 投资信息
  investmentExperience?: 'beginner' | 'intermediate' | 'advanced' | 'professional'
  riskTolerance?: 'conservative' | 'moderate' | 'aggressive'
  investmentGoals?: string[]

  // 其他信息
  bio?: string
  interests?: string[]
}

// 用户偏好设置
export interface UserPreferences {
  // 界面设置
  theme: 'light' | 'dark' | 'auto'
  language: string
  currency: string

  // 通知设置
  notifications: {
    email: boolean
    sms: boolean
    push: boolean
    tradingAlerts: boolean
    marketNews: boolean
    systemNotifications: boolean
  }

  // 交易设置
  trading: {
    defaultOrderType: 'market' | 'limit'
    confirmOrders: boolean
    autoRefresh: boolean
    showAdvancedFeatures: boolean
  }

  // 图表设置
  charts: {
    defaultTimeframe: string
    candlestickStyle: 'candle' | 'line' | 'bar'
    showVolume: boolean
    showIndicators: boolean
    colorScheme: 'red-green' | 'green-red'
  }

  // 数据设置
  data: {
    autoSave: boolean
    dataRetention: number // days
    enableAnalytics: boolean
  }
}

// 登录凭据
export interface LoginCredentials {
  username: string
  password: string
  captcha?: string
  remember?: boolean
  verification_token?: string // 滑轨验证令牌
}

// 登录数据 (别名)
export type LoginData = LoginCredentials

// 注册数据
export interface RegisterData {
  username: string
  password: string
  confirmPassword: string
  email: string
  phone?: string
  captcha: string
  inviteCode?: string
  agreeTerms: boolean
}

// 注册凭据（别名）
export type RegisterCredentials = RegisterData

// 登录响应
export interface LoginResponse {
  success: boolean
  message?: string
  data: {
    accessToken: string
    refreshToken: string
    userInfo: User
  }
}

// 刷新token响应
export interface RefreshTokenResponse {
  success: boolean
  message?: string
  data: {
    accessToken: string
    refreshToken: string
  }
}

// 用户信息类型（别名）
export type UserInfo = User

// 密码修改数据
export interface ChangePasswordData {
  oldPassword: string
  newPassword: string
  confirmPassword: string
}

// 认证令牌
export interface AuthTokens {
  accessToken: string
  refreshToken: string
  tokenType: string
  expiresIn: number
}

// 用户权限
export interface UserPermission {
  id: string
  name: string
  description: string
  category: string
  resource: string
  actions: string[]
}

// 用户角色权限
export interface UserRolePermissions {
  role: UserRole
  permissions: UserPermission[]
}

// 用户活动日志
export interface UserActivity {
  id: string
  userId: string
  type: 'login' | 'logout' | 'trade' | 'deposit' | 'withdraw' | 'profile_update'
  description: string
  ip: string
  userAgent: string
  timestamp: string
  metadata?: Record<string, any>
}

// 用户验证
export interface UserVerification {
  type: 'email' | 'phone' | 'identity'
  status: 'pending' | 'verified' | 'failed'
  code?: string
  expiresAt?: string
  verifiedAt?: string
}

// 用户安全设置
export interface UserSecurity {
  twoFactorEnabled: boolean
  securityQuestions: Array<{
    question: string
    answer: string // 加密存储
  }>
  trustedDevices: Array<{
    id: string
    name: string
    lastUsed: string
    ip: string
  }>
  loginHistory: Array<{
    timestamp: string
    ip: string
    userAgent: string
    success: boolean
  }>
}

// 用户订阅
export interface UserSubscription {
  id: string
  userId: string
  planId: string
  planName: string
  status: 'active' | 'cancelled' | 'expired' | 'trial'
  startDate: string
  endDate: string
  features: string[]
  price: number
  currency: string
  paymentMethod: string
}

// 用户统计
export interface UserStats {
  // 基本统计
  totalLogins: number
  totalTrades: number
  totalStrategies: number
  totalBacktests: number

  // 活跃度
  loginStreak: number
  lastActiveDate: string

  // 交易统计
  totalPnL: number
  winRate: number
  bestStrategy: string

  // 使用统计
  favoriteFeatures: string[]
  avgSessionDuration: number
}

// 用户反馈
export interface UserFeedback {
  id: string
  userId: string
  type: 'bug' | 'feature' | 'general' | 'complaint'
  title: string
  content: string
  rating?: number
  status: 'pending' | 'processing' | 'resolved' | 'closed'
  attachments?: string[]
  createdAt: string
  response?: string
  responseAt?: string
}

// 用户邀请
export interface UserInvitation {
  id: string
  inviterId: string
  inviterName: string
  email: string
  code: string
  status: 'pending' | 'accepted' | 'expired'
  createdAt: string
  acceptedAt?: string
  reward?: {
    type: 'commission' | 'bonus' | 'feature'
    value: number
    currency?: string
  }
}

// 滑轨验证相关类型
export interface SliderCaptchaChallenge {
  challenge_id: string
  background_image: string
  slider_image: string
  slider_width: number
  slider_height: number
  background_width: number
  background_height: number
  correct_position: number
}

export interface SliderTrajectoryPoint {
  x: number
  y: number
  timestamp: number
}

export interface SliderVerificationData {
  challenge_id: string
  slider_position: number
  time_taken: number
  trajectory: SliderTrajectoryPoint[]
}

export interface SliderVerificationResult {
  success: boolean
  verification_token?: string
  message: string
  error_code?: string
}

export interface SliderCaptchaState {
  challenge: SliderCaptchaChallenge | null
  isLoading: boolean
  isDragging: boolean
  isVerified: boolean
  verificationToken: string | null
  errorMessage: string | null
  startTime: number
  trajectory: SliderTrajectoryPoint[]
}
