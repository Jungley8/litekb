// API 基础配置
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    const { response } = error
    if (response?.status === 401) {
      // Token 过期，尝试刷新
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const { access_token } = await authApi.refresh(refreshToken)
          localStorage.setItem('token', access_token)
          // 重试请求
          error.config.headers.Authorization = `Bearer ${access_token}`
          return api.request(error.config)
        } catch {
          // 刷新失败，跳转登录
          localStorage.removeItem('token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)
