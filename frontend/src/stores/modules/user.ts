import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginData } from '@/types/user'
import { authService } from '@/services/auth.service'
import { ElMessage } from 'element-plus'
import router from '@/router'

export const useUserStore = defineStore('user', () => {
  // 状态
  const userInfo = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const isLoggedIn = ref(false)
  const permissions = ref<string[]>([])
  const preferences = ref({
    theme: 'light',
    language: 'zh-CN',
    notifications: true,
    autoSave: true
  })

  // 计算属性
  const isVip = computed(() => userInfo.value?.isVip || false)
  const hasPermission = computed(() => (permission: string) => {
    return permissions.value.includes(permission) || permissions.value.includes('*')
  })

  // 登录
  const login = async (loginData: LoginData) => {
    try {
      const { user, token: accessToken } = await authService.login(loginData as any)

      // 保存用户信息和token
      userInfo.value = user
      token.value = accessToken
      isLoggedIn.value = true
      permissions.value = user.permissions || []
      
      // 保存到本地存储
      localStorage.setItem('token', accessToken)
      localStorage.setItem('userInfo', JSON.stringify(user))
      
      ElMessage.success('登录成功')
      return { user, token: accessToken }
    } catch (error) {
      ElMessage.error('登录失败')
      throw error
    }
  }

  // 注册
  const register = async (registerData: any) => {
    try {
      const payload = {
        username: registerData.username,
        email: registerData.email,
        password: registerData.password,
        confirm_password: registerData.confirmPassword || registerData.password,
        full_name: registerData.fullName
      }

      await authService.register(payload as any)
      // 注册成功后不自动登录，交由调用方决定
      return true
    } catch (error) {
      ElMessage.error('注册失败')
      throw error
    }
  }

  // 发送重置密码验证码
  const sendResetCode = async (email: string) => {
    try {
      await authService.sendResetCode(email)
    } catch (error) {
      throw error
    }
  }

  // 重置密码
  const resetPassword = async (data: { email: string; code: string }) => {
    try {
      await authService.resetPassword({ email: data.email, code: data.code, newPassword: '' } as any)
    } catch (error) {
      throw error
    }
  }

  // 登出
  const logout = async () => {
    try {
      if (token.value) {
        await authService.logout()
      }
    } catch (error) {
      console.warn('Logout API failed:', error)
    } finally {
      // 清除状态
      userInfo.value = null
      token.value = null
      isLoggedIn.value = false
      permissions.value = []
      
      // 清除本地存储
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      
      ElMessage.success('已退出登录')
      
      // 强制重载页面，以便路由守卫重新检查并重定向到登录页
      router.replace('/login').catch(() => {})
    }
  }

  // 获取用户信息
  const getUserInfo = async () => {
    try {
      const user = await authService.getUserProfile()
      userInfo.value = user
      permissions.value = user.permissions || []
      return user
    } catch (error) {
      ElMessage.error('获取用户信息失败')
      throw error
    }
  }

  // 更新用户信息
  const updateUserInfo = async (data: Partial<User>) => {
    try {
      const updatedUser = await authService.updateProfile(data)
      userInfo.value = { ...userInfo.value, ...updatedUser }
      
      // 更新本地存储
      localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
      
      ElMessage.success('用户信息更新成功')
      return updatedUser
    } catch (error) {
      ElMessage.error('更新用户信息失败')
      throw error
    }
  }

  // 修改密码
  const changePassword = async (oldPassword: string, newPassword: string) => {
    try {
      await authService.changePassword(oldPassword, newPassword)
      ElMessage.success('密码修改成功')
    } catch (error) {
      ElMessage.error('密码修改失败')
      throw error
    }
  }

  // 更新偏好设置
  const updatePreferences = (newPreferences: Partial<typeof preferences.value>) => {
    preferences.value = { ...preferences.value, ...newPreferences }
    localStorage.setItem('userPreferences', JSON.stringify(preferences.value))
  }

  // 初始化用户状态
  const initUserState = () => {
    // 从本地存储恢复用户信息
    const savedUserInfo = localStorage.getItem('userInfo')
    const savedToken = localStorage.getItem('token')
    const savedPreferences = localStorage.getItem('userPreferences')
    
    if (savedUserInfo && savedToken) {
      try {
        userInfo.value = JSON.parse(savedUserInfo)
        token.value = savedToken
        isLoggedIn.value = true
        permissions.value = userInfo.value?.permissions || []
      } catch (error) {
        console.error('Failed to parse saved user info:', error)
        // 清除无效数据
        localStorage.removeItem('userInfo')
        localStorage.removeItem('token')
      }
    }
    
    if (savedPreferences) {
      try {
        preferences.value = { ...preferences.value, ...JSON.parse(savedPreferences) }
      } catch (error) {
        console.error('Failed to parse saved preferences:', error)
      }
    }
  }

  // 检查权限
  const checkPermission = (permission: string): boolean => {
    return hasPermission.value(permission)
  }

  // 检查多个权限（需要全部满足）
  const checkPermissions = (permissionList: string[]): boolean => {
    return permissionList.every(permission => checkPermission(permission))
  }

  // 检查任一权限（满足其中一个即可）
  const checkAnyPermission = (permissionList: string[]): boolean => {
    return permissionList.some(permission => checkPermission(permission))
  }

  // 刷新token
  const refreshToken = async () => {
    try {
      const { token: newToken } = await authService.refreshToken()
      token.value = newToken
      localStorage.setItem('token', newToken)
      return newToken
    } catch (error) {
      // token刷新失败，需要重新登录
      await logout()
      throw error
    }
  }

  return {
    // 状态
    userInfo,
    token,
    isLoggedIn,
    permissions,
    preferences,
    
    // 计算属性
    isVip,
    hasPermission,
    
    // 方法
    login,
    logout,
    getUserInfo,
    updateUserInfo,
    changePassword,
    updatePreferences,
    initUserState,
    checkPermission,
    checkPermissions,
    checkAnyPermission,
    refreshToken,
    register,
    sendResetCode,
    resetPassword
  }
}) 