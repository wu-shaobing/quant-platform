/**
 * 认证相关组合式函数
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/modules/user'
import { 
  getToken, 
  hasToken, 
  isTokenExpired, 
  isTokenExpiringSoon,
  clearAuth,
  hasPermission,
  hasAnyPermission,
  hasAllPermissions
} from '@/utils/auth'

export const useAuth = () => {
  const router = useRouter()
  const userStore = useUserStore()
  
  const loading = ref(false)
  const refreshing = ref(false)
  
  // 计算属性
  const isAuthenticated = computed(() => userStore.isAuthenticated)
  const currentUser = computed(() => userStore.currentUser)
  const userPermissions = computed(() => userStore.permissions)
  
  /**
   * 登录
   */
  const login = async (credentials: {
    username: string
    password: string
    captcha?: string
    rememberMe?: boolean
  }) => {
    loading.value = true
    
    try {
      await userStore.login(credentials)
      ElMessage.success('登录成功')
      
      // 跳转到首页或之前访问的页面
      const redirect = router.currentRoute.value.query.redirect as string
      await router.push(redirect || '/dashboard')
      
    } catch (error) {
      console.error('登录失败:', error)
      ElMessage.error(error instanceof Error ? error.message : '登录失败')
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 登出
   */
  const logout = async () => {
    try {
      await userStore.logout()
      ElMessage.success('已退出登录')
      await router.push('/login')
    } catch (error) {
      console.error('登出失败:', error)
      // 即使登出失败也要清除本地状态
      clearAuth()
      await router.push('/login')
    }
  }
  
  /**
   * 刷新Token
   */
  const refreshToken = async () => {
    if (refreshing.value) return
    
    refreshing.value = true
    
    try {
      await userStore.refreshToken()
    } catch (error) {
      console.error('刷新Token失败:', error)
      // 刷新失败，跳转到登录页
      await logout()
      throw error
    } finally {
      refreshing.value = false
    }
  }
  
  /**
   * 检查认证状态
   */
  const checkAuth = async () => {
    const token = getToken()
    
    if (!token) {
      return false
    }
    
    if (isTokenExpired(token)) {
      try {
        await refreshToken()
        return true
      } catch {
        return false
      }
    }
    
    // Token即将过期，尝试刷新
    if (isTokenExpiringSoon(token)) {
      try {
        await refreshToken()
      } catch {
        // 刷新失败但Token还未过期，继续使用
      }
    }
    
    return true
  }
  
  /**
   * 检查权限
   */
  const checkPermission = (permission: string): boolean => {
    return hasPermission(permission)
  }
  
  /**
   * 检查任一权限
   */
  const checkAnyPermission = (permissions: string[]): boolean => {
    return hasAnyPermission(permissions)
  }
  
  /**
   * 检查所有权限
   */
  const checkAllPermissions = (permissions: string[]): boolean => {
    return hasAllPermissions(permissions)
  }
  
  /**
   * 获取用户信息
   */
  const getUserInfo = async () => {
    try {
      await userStore.getUserInfo()
    } catch (error) {
      console.error('获取用户信息失败:', error)
      throw error
    }
  }
  
  /**
   * 更新用户信息
   */
  const updateUserInfo = async (userInfo: Record<string, unknown>) => {
    try {
      await userStore.updateUserInfo(userInfo)
      ElMessage.success('用户信息更新成功')
    } catch (error) {
      console.error('更新用户信息失败:', error)
      ElMessage.error(error instanceof Error ? error.message : '更新失败')
      throw error
    }
  }
  
  /**
   * 修改密码
   */
  const changePassword = async (data: {
    oldPassword: string
    newPassword: string
    confirmPassword: string
  }) => {
    if (data.newPassword !== data.confirmPassword) {
      throw new Error('两次输入的密码不一致')
    }
    
    try {
      await userStore.changePassword(data)
      ElMessage.success('密码修改成功，请重新登录')
      await logout()
    } catch (error) {
      console.error('修改密码失败:', error)
      ElMessage.error(error instanceof Error ? error.message : '修改密码失败')
      throw error
    }
  }
  
  /**
   * 忘记密码
   */
  const forgotPassword = async (email: string) => {
    try {
      await userStore.forgotPassword(email)
      ElMessage.success('重置密码邮件已发送')
    } catch (error) {
      console.error('发送重置邮件失败:', error)
      ElMessage.error(error instanceof Error ? error.message : '发送失败')
      throw error
    }
  }
  
  /**
   * 重置密码
   */
  const resetPassword = async (data: {
    token: string
    password: string
    confirmPassword: string
  }) => {
    if (data.password !== data.confirmPassword) {
      throw new Error('两次输入的密码不一致')
    }
    
    try {
      await userStore.resetPassword(data)
      ElMessage.success('密码重置成功，请登录')
      await router.push('/login')
    } catch (error) {
      console.error('重置密码失败:', error)
      ElMessage.error(error instanceof Error ? error.message : '重置密码失败')
      throw error
    }
  }
  
  // 初始化时检查认证状态
  onMounted(async () => {
    if (hasToken()) {
      try {
        await checkAuth()
        if (isAuthenticated.value && !currentUser.value) {
          await getUserInfo()
        }
      } catch (error) {
        console.error('初始化认证状态失败:', error)
      }
    }
  })
  
  return {
    // 状态
    loading,
    refreshing,
    isAuthenticated,
    currentUser,
    userPermissions,
    
    // 方法
    login,
    logout,
    refreshToken,
    checkAuth,
    checkPermission,
    checkAnyPermission,
    checkAllPermissions,
    getUserInfo,
    updateUserInfo,
    changePassword,
    forgotPassword,
    resetPassword
  }
}