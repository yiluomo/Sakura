import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'

// ⚠️ 前端仅以桌面/移动应用形式分发，不对外公开部署，Token 可安全硬编码
// 如需更换 Token，后端同步修改 config.py 中的 API_TOKEN 即可
const API_TOKEN = 'sakura-private-token-a7f3k9z2m1p8q4w6'

export interface ApiResponse<T> {
  data: T
  success?: boolean
  message?: string
}

class ApiClient {
  public client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // 请求拦截器：自动注入 API Token
    this.client.interceptors.request.use(
      config => {
        config.headers['X-API-Token'] = API_TOKEN
        return config
      },
      error => Promise.reject(error)
    )

    // 响应拦截器
    this.client.interceptors.response.use(
      response => response,
      error => {
        // 增强错误信息
        if (error.response) {
          // 服务器返回错误状态码
          error.message = error.response.data?.msg || error.response.data?.message || error.message
        } else if (error.request) {
          // 请求已发送但没有收到响应
          error.code = 'ERR_NETWORK'
          error.message = '网络连接失败'
        }

        console.error('API Error:', {
          url: error.config?.url,
          status: error.response?.status,
          message: error.message
        })

        return Promise.reject(error)
      }
    )
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.get(url, config)
    return { data: response.data }
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.post(url, data, config)
    return { data: response.data }
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.put(url, data, config)
    return { data: response.data }
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.delete(url, config)
    return { data: response.data }
  }
}

export const apiClient = new ApiClient()
