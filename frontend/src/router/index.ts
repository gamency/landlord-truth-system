import { createRouter, createWebHistory } from 'vue-router'
import PropertyView from '../views/PropertyView.vue'
import BillingView from '../views/BillingView.vue'
import MeterReadingView from '../views/MeterReadingView.vue'
import DashboardView from '../views/DashboardView.vue'



// 其他页面以后再加
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' }, // 默认首页改为看板
    { path: '/dashboard', name: 'Dashboard', component: DashboardView },
    { path: '/property', name: 'Property', component: PropertyView },
    { path: '/billing', name: 'Billing', component: BillingView }, // 新增
    { path: '/meter-reading', name: 'MeterReading', component: MeterReadingView },

  ]
})
export default router

