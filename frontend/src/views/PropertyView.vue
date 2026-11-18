<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const properties = ref<any[]>([])
const activeProperty = ref<any>(null)
const rooms = ref<any[]>([])
const loading = ref(false)

// 获取楼栋
const fetchProperties = async () => {
  const res = await axios.get('/api/v1/property/properties')
  properties.value = res.data.data
  if (properties.value.length > 0 && !activeProperty.value) {
    selectProperty(properties.value[0])
  }
}

// 选中楼栋并获取房间
const selectProperty = async (prop: any) => {
  activeProperty.value = prop
  loading.value = true
  try {
    const res = await axios.get(`/api/v1/property/properties/${prop.property_id}/rooms`)
    rooms.value = res.data.data
  } catch (e) {
    console.error('获取房间失败', e)
    rooms.value = []
  } finally {
    loading.value = false
  }
}

// 新建楼栋
const handleCreateProperty = async () => {
  const name = prompt('请输入楼栋名称（如：幸福小区2栋）：')
  if (!name) return
  const address = prompt('请输入楼栋地址：')
  if (!address) return
  
  await axios.post('/api/v1/property/properties', {
    property_name: name,
    address: address,
    property_type: 'SELF_BUILT'
  })
  fetchProperties() // 刷新列表
}

// 添加房间
const handleCreateRoom = async () => {
  if (!activeProperty.value) return alert('请先选择楼栋')
  const roomNumber = prompt('请输入房间号（如：204）：')
  if (!roomNumber) return
  
  await axios.post(`/api/v1/property/properties/${activeProperty.value.property_id}/rooms`, {
    room_number: roomNumber,
    room_type: 'RENTAL',
    room_name: roomNumber + '房'
  })
  selectProperty(activeProperty.value) // 刷新房间列表
}

onMounted(fetchProperties)
</script>

<template>
  <div>
    <div class="page-header">
      <h1>房源管理</h1>
      <button class="btn-primary" @click="handleCreateProperty">+ 新建楼栋</button>
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
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h3>{{ activeProperty?.property_name }} - 房间列表</h3>
          <button class="btn-primary" style="padding: 6px 12px; font-size: 14px;" @click="handleCreateRoom">+ 添加房间</button>
        </div>
        
        <div v-if="loading" style="margin-top: 20px; color: #86909c;">正在加载房间数据...</div>
        
        <div v-else-if="rooms.length === 0" style="margin-top: 20px; color: #86909c;">
          该楼栋下还没有房间，点击右上角“添加房间”试试。
        </div>

        <div v-else class="room-grid">
          <div 
            v-for="room in rooms" 
            :key="room.room_id"
            :class="['room-card', room.room_status === 'VACANT' ? 'vacant' : 'occupied']"
          >
            <h4>{{ room.room_name || room.room_number }}</h4>
            <p>{{ room.room_type === 'RENTAL' ? '出租房' : room.room_type }}</p>
            <span class="status">
              {{ room.room_status === 'VACANT' ? '空置' : '已租' }}
            </span>
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