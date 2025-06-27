/**
 * HTTP 请求客户端配置
 */
import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig, AxiosError } from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/modules/user'

// 响应数据类型
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
  timestamp?: number
  requestId?: string
}

// 请求配置扩展
export interface RequestConfig extends AxiosRequestConfig {
  skipAuth?: boolean      // 跳过认证
  skipErrorHandler?: boolean  // 跳过错误处理
  showLoading?: boolean   // 显示加载状态
  showError?: boolean     // 显示错误提示
  retryCount?: number     // 重试次数
}

// 生成请求ID
const generateRequestId = (): string => {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

// 创建axios实例
const createHttpClient = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: import.meta.env['VITE_API_BASE_URL'] || 'http://localhost:8000/api',
    timeout: Number(import.meta.env['VITE_API_TIMEOUT']) || 10000,
    headers: {
      'Content-Type': 'application/json'
    }
  })

  // 请求拦截器
  instance.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      const userStore = useUserStore()

      // 添加认证token
      const token = userStore.token
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`
      }

      // 添加请求ID用于追踪
      config.headers['X-Request-ID'] = generateRequestId()

      // 添加时间戳防止缓存
      if (config.method === 'get') {
        config.params = {
          ...config.params,
          _t: Date.now()
        }
      }

      return config
    },
    (error: AxiosError) => {
      console.error('请求拦截器错误:', error)
      return Promise.reject(error)
    }
  )

  // 响应拦截器
  instance.interceptors.response.use(
    (response: AxiosResponse) => {
      const { data } = response

      // 统一处理响应格式
      if (data.code !== undefined && data.code !== 200) {
        ElMessage.error(data.message || '请求失败')
        return Promise.reject(new Error(data.message))
      }
      
      return data.data || data
    },
    async (error: AxiosError) => {
      const { response, config } = error

      if (response) {
        switch (response.status) {
          case 401:
            // Token过期，尝试刷新
            if (!config?.url?.includes('/auth/refresh')) {
                try {
                    await useUserStore().refreshToken()
                    // 重新发送原请求
                    return instance(config!)
                } catch {
                    useUserStore().logout()
                    ElMessageBox.confirm(
                        '您的登录已过期，请重新登录。',
                        '登录过期',
                        {
                            confirmButtonText: '重新登录',
                            cancelButtonText: '取消',
                            type: 'warning'
                        }
                    ).then(() => {
                        window.location.href = '/login'
                    })
                }
            } else {
                 useUserStore().logout()
            }
            break
            
          case 403:
            ;(ElMessage as any).error('没有权限访问该资源')
            break
            
          case 404:
            ;(ElMessage as any).error('请求的资源不存在')
            break
            
          case 500:
            ;(ElMessage as any).error('服务器内部错误')
            break
            
          default:
            ;(ElMessage as any).error(`请求失败: ${response.status}`)
        }
      } else {
        ;(ElMessage as any).error('网络连接失败')
      }
      
      return Promise.reject(error)
    }
  )

  return instance
}

export const http = createHttpClient()

export default http 