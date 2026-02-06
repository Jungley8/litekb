import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import KnowledgeBases from './views/KnowledgeBases.vue'
import KBDetail from './views/KBDetail.vue'
import Chat from './views/Chat.vue'
import Search from './views/Search.vue'
import Graph from './views/Graph.vue'
import Settings from './views/Settings.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: Home
  },
  {
    path: '/kbs',
    name: 'kbs',
    component: KnowledgeBases
  },
  {
    path: '/kb/:id',
    name: 'kbDetail',
    component: KBDetail
  },
  {
    path: '/chat',
    name: 'chat',
    component: Chat
  },
  {
    path: '/search',
    name: 'search',
    component: Search
  },
  {
    path: '/graph',
    name: 'graph',
    component: Graph
  },
  {
    path: '/settings',
    name: 'settings',
    component: Settings
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
