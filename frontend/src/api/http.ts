/**
 * HTTP 请求客户端配置
 */
import axios, { 
  type AxiosInstance, 
  type AxiosRequestConfig, 
  type AxiosResponse, 
  type AxiosError,
  type InternalAxiosRequestConfig
} from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import router from '@/router'
import { useUserStore } from '@/stores/modules/user'
import type { ApiResponse, ApiError, RequestConfig } from '@/types/api'

// 创建axios实例
const http: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求重试配置
interface RetryConfig {
  retries: number
  retryDelay: number
  retryCondition?: (error: AxiosError) => boolean
}

const defaultRetryConfig: RetryConfig = {
  retries: 3,
  retryDelay: 1000,
  retryCondition: (error: AxiosError) => {
    return !error.response || (error.response.status >= 500 && error.response.status < 600)
  }
}

// 添加重试功能
const addRetryInterceptor = (instance: AxiosInstance, config: RetryConfig = defaultRetryConfig) => {
  instance.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      const { retries, retryDelay, retryCondition } = config
      const requestConfig = error.config as InternalAxiosRequestConfig & { __retryCount?: number }
      
      if (!requestConfig || !retryCondition?.(error)) {
        return Promise.reject(error)
      }
      
      requestConfig.__retryCount = requestConfig.__retryCount || 0
      
      if (requestConfig.__retryCount >= retries) {
        return Promise.reject(error)
      }
      
      requestConfig.__retryCount += 1
      
      await new Promise(resolve => setTimeout(resolve, retryDelay * requestConfig.__retryCount))
      
      return instance(requestConfig)
    }
  )
}

// 应用重试拦截器
addRetryInterceptor(http)

// 请求拦截器
http.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 添加认证token
    const userStore = useUserStore()
    const token = userStore.token
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // 添加请求ID用于追踪
    config.headers['X-Request-ID'] = generateRequestId()
    
    // 添加时间戳
    config.headers['X-Timestamp'] = Date.now().toString()
    
    console.log(`[HTTP Request] ${config.method?.toUpperCase()} ${config.url}`, {
      headers: config.headers,
      data: config.data,
      params: config.params
    })
    
    return config
  },
  (error: AxiosError) => {
    console.error('[HTTP Request Error]', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
http.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    console.log(`[HTTP Response] ${response.config.method?.toUpperCase()} ${response.config.url}`, {
      status: response.status,
      data: response.data
    })
    
    // 检查业务状态码
    if (response.data && typeof response.data === 'object' && 'success' in response.data) {
      if (!response.data.success) {
        const error = new Error(response.data.message || '请求失败') as any
        error.code = response.data.code
        error.response = response
        return Promise.reject(error)
      }
    }
    
    return response
  },
  async (error: AxiosError<ApiError>) => {
    console.error('[HTTP Response Error]', {
      status: error.response?.status,
      data: error.response?.data,
      config: error.config
    })
    
    const userStore = useUserStore()
    
    // 处理不同的HTTP状态码
    switch (error.response?.status) {
      case 401:
        // 未授权，清除token并跳转到登录页
        ElMessage.error('登录已过期，请重新登录')
        await userStore.logout()
        router.push('/login')
        break
        
      case 403:
        // 禁止访问
        ElMessage.error('没有权限访问该资源')
        break
        
      case 404:
        // 资源不存在
        ElMessage.error('请求的资源不存在')
        break
        
      case 422:
        // 数据验证错误
        const validationError = error.response.data
        if (validationError?.details) {
          const firstError = Object.values(validationError.details)[0]
          ElMessage.error(firstError as string || '数据验证失败')
        } else {
          ElMessage.error(validationError?.message || '数据验证失败')
        }
        break
        
      case 429:
        // 请求过于频繁
        ElMessage.warning('请求过于频繁，请稍后再试')
        break
        
      case 500:
        // 服务器内部错误
        ElMessage.error('服务器内部错误，请稍后再试')
        break
        
      case 502:
      case 503:
      case 504:
        // 服务不可用
        ElMessage.error('服务暂时不可用，请稍后再试')
        break
        
      default:
        // 网络错误或其他错误
        if (!error.response) {
          ElMessage.error('网络连接失败，请检查网络设置')
        } else {
          const message = error.response.data?.message || error.message || '请求失败'
          ElMessage.error(message)
        }
    }
    
    return Promise.reject(error)
  }
)

// 生成请求ID
function generateRequestId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

// 创建带有特定配置的请求函数
export function createRequest(config: RequestConfig = {}) {
  const instance = axios.create({
    ...http.defaults,
    timeout: config.timeout || http.defaults.timeout,
    headers: {
      ...http.defaults.headers,
      ...config.headers
    }
  })
  
  // 复制拦截器
  instance.interceptors.request = http.interceptors.request
  instance.interceptors.response = http.interceptors.response
  
  if (config.retries !== undefined) {
    addRetryInterceptor(instance, {
      retries: config.retries,
      retryDelay: config.retryDelay || 1000
    })
  }
  
  return instance
}

// 封装常用的HTTP方法
export const httpClient = {
  get: <T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> => {
    return http.get(url, config)
  },
  
  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> => {
    return http.post(url, data, config)
  },
  
  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> => {
    return http.put(url, data, config)
  },
  
  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> => {
    return http.patch(url, data, config)
  },
  
  delete: <T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> => {
    return http.delete(url, config)
  }
}

// 文件上传
export const uploadFile = async (
  url: string, 
  file: File, 
  onProgress?: (progress: number) => void
): Promise<AxiosResponse<ApiResponse>> => {
  const formData = new FormData()
  formData.append('file', file)
  
  return http.post(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(progress)
      }
    }
  })
}

// 下载文件
export const downloadFile = async (url: string, filename?: string): Promise<void> => {
  try {
    const response = await http.get(url, {
      responseType: 'blob'
    })
    
    const blob = new Blob([response.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  } catch (error) {
    console.error('文件下载失败:', error)
    ElMessage.error('文件下载失败')
  }
}

// 批量请求
export const batchRequest = async <T = any>(
  requests: Array<() => Promise<AxiosResponse<ApiResponse<T>>>>
): Promise<Array<AxiosResponse<ApiResponse<T>> | Error>> => {
  return Promise.allSettled(requests.map(request => request())).then(results =>
    results.map(result => 
      result.status === 'fulfilled' ? result.value : result.reason
    )
  )
}

// 取消请求的控制器
export class RequestController {
  private controllers: Map<string, AbortController> = new Map()
  
  create(key: string): AbortController {
    this.cancel(key) // 取消之前的请求
    const controller = new AbortController()
    this.controllers.set(key, controller)
    return controller
  }
  
  cancel(key: string): void {
    const controller = this.controllers.get(key)
    if (controller) {
      controller.abort()
      this.controllers.delete(key)
    }
  }
  
  cancelAll(): void {
    this.controllers.forEach(controller => controller.abort())
    this.controllers.clear()
  }
}

export default http

// 为了兼容现有的导入语句，同时导出命名导出
export { http } 