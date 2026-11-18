<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

// 楼栋数据
const properties = ref<any[]>([])
// 当前选中的楼栋
const activeProperty = ref<any>(null)
// 当前楼栋下的房间
const rooms = ref<any[]>([])

// 获取楼栋列表
const fetchProperties = async () => {
  const res = await axios.get('/api/v1/property/properties')
  properties.value = res.data.data
  if (properties.value.length > 0 && !activeProperty.value) {
    selectProperty(properties.value[0])
  }
}

// 选中楼栋，加载房间
const selectProperty = async (prop: any) => {
  activeProperty.value = prop
  // 此处需要后端补充一个查询房间的接口，我们先假设接口是这样，如果报错，我们稍后再处理
  try {
    const res = await axios.get(`/api/v1/property/properties/${prop.property_id}/rooms`)
    rooms.value = res.data.data
  } catch (e) {
    // 如果后端还没写这个接口，先给个空数组兜底
    rooms.value = []
  }
}

onMounted(fetchProperties)
</script>

<template>
  <div>
    <div class="page-header">
      <h1>房源管理</h1>
      <button class="btn-primary">+ 新建楼栋</button>
    </div>

    <div class="property-layout">
      <!-- 楼栋列表 -->
      <div class="property-list">
        <h3>楼栋列表</h3>
        <div 
          v-for="p in properties" 
          :key="p.property_id"
          :class="['property-card', { active: activeProperty?.property_id === p.property_id }]"
          @click="selectProperty(p)"
        >
          {{ p.property_name }}
        </div>
      </div>

      <!-- 房间网格 -->
      <div class="room-grid-container">
        <h3>{{ activeProperty?.property_name }} - 房间列表</h3>
        <div class="room-grid">
          <!-- 这里用之前的文档数据做演示，因为后端可能还没写查房间的接口 -->
          <div class="room-card vacant">
            <h4>201房</h4>
            <p>出租房</p>
            <span class="status">空置</span>
          </div>
          <div class="room-card occupied">
            <h4>202房</h4>
            <p>出租房</p>
            <span class="status">已租</span>
          </div>
           <div class="room-card vacant">
            <h4>203房</h4>
            <p>出租房</p>
            <span class="status">空置</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.btn-primary { background: #1677ff; color: white; border: none; padding: 10px 16px; border-radius: 4px; cursor: pointer; }
.property-layout { display: flex; gap: 20px; }
.property-list { width: 250px; background: white; padding: 16px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.property-card { padding: 12px; border: 1px solid #e5e6eb; margin-bottom: 8px; border-radius: 4px; cursor: pointer; transition: 0.2s; }
.property-card:hover { border-color: #1677ff; }
.property-card.active { background: #e8f3ff; border-color: #1677ff; color: #1677ff; font-weight: bold; }

.room-grid-container { flex: 1; background: white; padding: 16px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.room-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 16px; margin-top: 16px; }
.room-card { border: 1px solid #e5e6eb; padding: 16px; border-radius: 8px; text-align: center; position: relative; }
.room-card h4 { margin-bottom: 8px; font-size: 18px; }
.room-card p { color: #86909c; font-size: 14px; }
.status { display: inline-block; margin-top: 12px; padding: 4px 8px; font-size: 12px; border-radius: 4px; }
.vacant .status { background: #f2f3f5; color: #86909c; }
.occupied .status { background: #e8ffea; color: #00b42a; }
</style>