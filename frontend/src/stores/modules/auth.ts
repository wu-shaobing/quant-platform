import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginCredentials, RegisterCredentials } from '@/types/user'
import { authService } from '@/services/auth.service'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const userRole = computed(() => user.value?.role || 'guest')
  const permissions = computed(() => user.value?.permissions || [])

  // Actions
  const login = async (credentials: LoginCredentials) => {
    try {
      isLoading.value = true
      error.value = null

      const response = await authService.login(credentials)

      user.value = response.user
      token.value = response.token

      localStorage.setItem('token', response.token)
      localStorage.setItem('user', JSON.stringify(response.user))

      return response
    } catch (err: any) {
      error.value = err.message || '登录失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const register = async (credentials: RegisterCredentials) => {
    try {
      isLoading.value = true
      error.value = null

      const response = await authService.register(credentials)

      user.value = response.user
      token.value = response.token

      localStorage.setItem('token', response.token)
      localStorage.setItem('user', JSON.stringify(response.user))

      return response
    } catch (err: any) {
      error.value = err.message || '注册失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const logout = async () => {
    try {
      if (token.value) {
        await authService.logout()
      }
    } catch (err) {
      console.warn('Logout request failed:', err)
    } finally {
      user.value = null
      token.value = null
      error.value = null

      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }

  const refreshToken = async () => {
    try {
      if (!token.value) return false

      const response = await authService.refreshToken()
      token.value = response.token

      localStorage.setItem('token', response.token)
      return true
    } catch (err) {
      await logout()
      return false
    }
  }

  const fetchUserProfile = async () => {
    try {
      if (!token.value) return

      const userProfile = await authService.getUserProfile()
      user.value = userProfile

      localStorage.setItem('user', JSON.stringify(userProfile))
    } catch (err) {
      console.error('Failed to fetch user profile:', err)
    }
  }

  const updateProfile = async (profileData: Partial<User>) => {
    try {
      isLoading.value = true

      const updatedUser = await authService.updateProfile(profileData)
      user.value = updatedUser

      localStorage.setItem('user', JSON.stringify(updatedUser))
      return updatedUser
    } catch (err: any) {
      error.value = err.message || '更新失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const changePassword = async (oldPassword: string, newPassword: string) => {
    try {
      isLoading.value = true
      error.value = null

      await authService.changePassword(oldPassword, newPassword)
    } catch (err: any) {
      error.value = err.message || '密码修改失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const hasPermission = (permission: string): boolean => {
    return permissions.value.includes(permission)
  }

  const hasRole = (role: string): boolean => {
    return userRole.value === role
  }

  const clearError = () => {
    error.value = null
  }

  // Initialize from localStorage
  const initializeAuth = () => {
    const storedUser = localStorage.getItem('user')
    if (storedUser && token.value) {
      try {
        user.value = JSON.parse(storedUser)
      } catch (err) {
        console.error('Failed to parse stored user:', err)
        logout()
      }
    }
  }

  return {
    // State
    user,
    token,
    isLoading,
    error,

    // Getters
    isAuthenticated,
    userRole,
    permissions,

    // Actions
    login,
    register,
    logout,
    refreshToken,
    fetchUserProfile,
    updateProfile,
    changePassword,
    hasPermission,
    hasRole,
    clearError,
    initializeAuth
  }
}, {
  persist: {
    key: 'auth-store',
    storage: localStorage,
    paths: ['user', 'token']
  }
})
