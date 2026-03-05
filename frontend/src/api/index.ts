import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'

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
    // 请求拦截器
    this.client.interceptors.request.use(
      config => config,
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
