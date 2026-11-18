import { createRouter, createWebHistory } from 'vue-router'
import PropertyView from '../views/PropertyView.vue'
import BillingView from '../views/BillingView.vue'
import MeterReadingView from '../views/MeterReadingView.vue'


// 其他页面以后再加
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/property' },
    { path: '/property', name: 'Property', component: PropertyView },
    { path: '/billing', name: 'Billing', component: BillingView }, // 新增
    { path: '/meter-reading', name: 'MeterReading', component: MeterReadingView },

  ]
})
export default router

