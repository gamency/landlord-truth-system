<script setup lang="ts">
import { ref, onMounted } from 'vue'

const properties = ref<any[]>([])
const loading = ref(false)
const error = ref('')

async function loadProperties() {
  loading.value = true
  error.value = ''
  try {
    const res = await fetch('/api/v1/property/properties')
    const json = await res.json()
    properties.value = json.data
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(loadProperties)
</script>

<template>
  <div style="padding: 20px; font-family: sans-serif;">
    <h1>房东经营真相系统 - 前端骨架</h1>
    <button @click="loadProperties" :disabled="loading">
      {{ loading ? '加载中...' : '刷新楼栋列表' }}
    </button>
    <p v-if="error" style="color: red;">错误：{{ error }}</p>
    <ul>
      <li v-for="p in properties" :key="p.property_id">
        {{ p.property_name }} - {{ p.address }} ({{ p.status }})
      </li>
    </ul>
    <p v-if="!loading && properties.length === 0">暂无楼栋数据</p>
  </div>
</template>