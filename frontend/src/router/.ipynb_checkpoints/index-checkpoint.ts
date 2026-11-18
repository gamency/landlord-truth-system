import { createRouter, createWebHistory } from 'vue-router'
import PropertyView from '../views/PropertyView.vue'
// 其他页面以后再加
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/property' },
    { path: '/property', name: 'Property', component: PropertyView },
  ]
})
export default router