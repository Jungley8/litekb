import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import naive from 'naive-ui'
import axios from 'axios'

// 全局样式
import './styles/main.css'

const app = createApp(App)

// 配置 axios
axios.defaults.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// 注册 naive-ui
app.use(naive)

// 注册路由
app.use(router)

// 全局错误处理
app.config.errorHandler = (err, vm, info) => {
  console.error('Global error:', err)
  console.error('Component:', vm)
  console.error('Info:', info)
}

app.mount('#app')
