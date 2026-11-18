<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const rooms = ref<any[]>([])
const readings = ref<any[]>([])
const loading = ref(false)

// 加载所有房间用于模拟拍照
const fetchRooms = async () => {
  const res = await axios.get('/api/v1/property/properties') // 先拿楼栋
  if (res.data.data.length > 0) {
    const propId = res.data.data[0].property_id
    const roomRes = await axios.get(`/api/v1/property/properties/${propId}/rooms`)
    rooms.value = roomRes.data.data
  }
}

// 获取识别记录
const fetchReadings = async () => {
  const res = await axios.get('/api/v1/property/readings')
  readings.value = res.data.data
}

// 模拟拍照上传
const simulateCapture = async (room: any) => {
  if (room.room_status === 'VACANT') return alert('空置房间无需抄表')
  loading.value = true
  try {
    await axios.post(`/api/v1/property/rooms/${room.room_id}/ocr-mock`)
    fetchReadings()
  } finally {
    loading.value = false
  }
}

// 一键连续拍照
const batchCapture = async () => {
  loading.value = true
  const occupiedRooms = rooms.value.filter(r => r.room_status === 'OCCUPIED')
  for (const room of occupiedRooms) {
    await axios.post(`/api/v1/property/rooms/${room.room_id}/ocr-mock`)
    await new Promise(r => setTimeout(r, 300)) // 模拟连续拍的间隔
  }
  loading.value = false
  fetchReadings()
}

// 人工修正
const correctReading = async (reading: any) => {
  const newValue = prompt(`请输入 ${reading.room_number} 房的真实电表读数：`, reading.value)
  if (newValue === null) return
  await axios.post(`/api/v1/property/readings/${reading.reading_id}/correct`, {
    value: parseFloat(newValue)
  })
  fetchReadings()
}

onMounted(() => {
  fetchRooms()
  fetchReadings()
})
</script>

<template>
  <div>
    <div class="page-header">
      <h1>AI 抄表工作台</h1>
      <button class="btn-primary" @click="batchCapture" :disabled="loading">
        {{ loading ? '正在连拍识别中...' : '📷 一键模拟连拍(所有在租房间)' }}
      </button>
    </div>

    <div class="layout">
      <!-- 左侧：模拟相机/房间列表 -->
      <div class="camera-panel">
        <h3>选择房间进行单拍</h3>
        <div class="room-tags">
          <button 
            v-for="r in rooms" 
            :key="r.room_id" 
            :disabled="r.room_status === 'VACANT' || loading"
            @click="simulateCapture(r)"
            :class="['tag', r.room_status === 'VACANT' ? 'disabled' : '']"
          >
            {{ r.room_number }}
          </button>
        </div>
      </div>

      <!-- 右侧：识别流水与异常处理 -->
      <div class="result-panel">
        <h3>识别结果与异常拦截</h3>
        <div v-if="readings.length === 0" class="empty">暂无识别记录</div>
        <table v-else class="data-table">
          <thead>
            <tr><th>时间</th><th>房间</th><th>识别值</th><th>置信度</th><th>状态</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="r in readings" :key="r.reading_id" :class="{ 'anomaly-row': r.status === 'ANOMALY' }">
              <td>{{ r.created_at }}</td>
              <td><strong>{{ r.room_number }}</strong></td>
              <td>{{ r.value }}</td>
              <td>{{ (r.confidence * 100).toFixed(1) }}%</td>
              <td>
                <span :class="['badge', r.status === 'SUCCESS' ? 'success' : (r.status === 'ANOMALY' ? 'danger' : 'warning')]">
                  {{ r.status === 'SUCCESS' ? '正常' : (r.status === 'ANOMALY' ? '读数倒挂' : '人工修正') }}
                </span>
              </td>
              <td>
                <button v-if="r.status === 'ANOMALY'" class="btn-small danger" @click="correctReading(r)">去修正</button>
                <span v-else-if="r.status === 'MANUALLY_CORRECTED'" style="color: #86909c; font-size: 12px;">已修正</span>
                <span v-else style="color: #00b42a; font-size: 12px;">已静默入库</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.btn-primary { background: #1677ff; color: white; border: none; padding: 10px 16px; border-radius: 4px; cursor: pointer; }
.layout { display: flex; gap: 20px; }
.camera-panel { width: 300px; background: white; padding: 20px; border-radius: 8px; }
.result-panel { flex: 1; background: white; padding: 20px; border-radius: 8px; }
.room-tags { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 16px; }
.tag { padding: 8px 16px; border: 1px solid #e5e6eb; border-radius: 4px; background: white; cursor: pointer; }
.tag:hover:not(.disabled) { border-color: #1677ff; color: #1677ff; }
.tag.disabled { background: #f2f3f5; color: #c9cdd4; cursor: not-allowed; }
.data-table { width: 100%; border-collapse: collapse; text-align: left; }
.data-table th, .data-table td { padding: 12px; border-bottom: 1px solid #e5e6eb; }
.data-table th { background: #f7f8fa; color: #4e5969; }
.badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
.badge.success { background: #e8ffea; color: #00b42a; }
.badge.danger { background: #ffece8; color: #f53f3f; }
.badge.warning { background: #fff7e8; color: #ff7d00; }
.anomaly-row { background: #fffafa; }
.btn-small { padding: 4px 10px; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; }
.btn-small.danger { background: #f53f3f; color: white; }
.empty { color: #86909c; text-align: center; margin-top: 50px; }
</style>