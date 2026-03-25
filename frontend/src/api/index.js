import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' }
})

// 请求拦截器：自动附加 JWT
api.interceptors.request.use(
  config => {
    if (config.skipAuth) {
      if (config.headers && config.headers.Authorization) {
        delete config.headers.Authorization
      }
      return config
    }
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器：统一错误处理
api.interceptors.response.use(
  response => response,
  async error => {
    const { response } = error
    if (response) {
      if (response.status === 401) {
        if (error.config?.skipAuth) {
          return Promise.reject(error)
        }
        // 尝试刷新 token
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken && !error.config._retry) {
          error.config._retry = true
          try {
            const res = await axios.post('/api/users/token/refresh/', {
              refresh: refreshToken
            })
            localStorage.setItem('access_token', res.data.access)
            if (res.data.refresh) {
              localStorage.setItem('refresh_token', res.data.refresh)
            }
            error.config.headers.Authorization = `Bearer ${res.data.access}`
            return api(error.config)
          } catch {
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            router.push('/login')
            ElMessage.error('登录已过期，请重新登录')
          }
        } else {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          router.push('/login')
        }
      } else if (response.status === 403) {
        ElMessage.error('没有权限执行此操作')
      } else if (response.status === 500) {
        ElMessage.error('服务器错误，请稍后重试')
      } else if (response.data) {
        const msg = typeof response.data === 'string'
          ? response.data
          : response.data.error || response.data.detail || JSON.stringify(response.data)
        ElMessage.error(msg)
      }
    } else {
      ElMessage.error('网络连接失败')
    }
    return Promise.reject(error)
  }
)

export default api
