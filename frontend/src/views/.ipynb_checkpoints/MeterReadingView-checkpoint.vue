<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'

const rooms = ref<any[]>([])
const readings = ref<any[]>([])
const loading = ref(false)

// 图表相关
const chartRef = ref<HTMLElement | null>(null)
let myChart: echarts.ECharts | null = null

// 文件上传相关
const selectedRoom = ref<any>(null)

const fetchRooms = async () => {
  const res = await axios.get('/api/v1/property/properties')
  if (res.data.data.length > 0) {
    const propId = res.data.data[0].property_id
    const roomRes = await axios.get(`/api/v1/property/properties/${propId}/rooms`)
    rooms.value = roomRes.data.data
  }
}

const fetchReadings = async () => {
  const res = await axios.get('/api/v1/metering/readings') // 注意路由变了
  readings.value = res.data.data
}

const fetchStatistics = async () => {
  const res = await axios.get('/api/v1/billing/statistics/water-electric')
  const data = res.data.data
  
  const months = data.map((d: any) => d.period)
  const external = data.map((d: any) => d.external)
  const internal = data.map((d: any) => d.internal)
  const loss = data.map((d: any) => d.loss)

  if (myChart) {
    myChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['外部真实成本', '内部收缴', '损耗差额'], bottom: 0 },
      grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
      xAxis: { type: 'category', data: months },
      yAxis: { type: 'value' },
      series: [
        { name: '外部真实成本', type: 'bar', data: external, itemStyle: { color: '#909399' } },
        { name: '内部收缴', type: 'bar', data: internal, itemStyle: { color: '#409EFF' } },
        { name: '损耗差额', type: 'line', data: loss, itemStyle: { color: '#F56C6C' }, smooth: true }
      ]
    })
  }
}

// 触发选图
const triggerUpload = (room: any) => {
  if (room.room_status === 'VACANT') return
  selectedRoom.value = room
  // 模拟点击 input
}

// 真实图片上传逻辑（此处用 el-upload 替代，见 template）
const handleFileUpload = async (options: any) => {
  const { file } = options
  if (!selectedRoom.value) return

  loading.value = true
  const formData = new FormData()
  formData.append('file', file)

  try {
    await axios.post(`/api/v1/metering/rooms/${selectedRoom.value.room_id}/ocr-upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    fetchReadings()
  } catch (e: any) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

// 修正异常读数
const correctReading = async (row: any) => {
  const { value } = await window.prompt('请输入真实电表读数：', row.value)
  if (!value) return
  await axios.post(`/api/v1/metering/readings/${row.reading_id}/correct`, { value: parseFloat(value) })
  fetchReadings()
}

onMounted(async () => {
  await fetchRooms()
  await fetchReadings()
  
  await nextTick()
  if (chartRef.value) {
    myChart = echarts.init(chartRef.value)
    fetchStatistics()
    // 监听窗口大小变化，图表自适应
    window.addEventListener('resize', () => myChart?.resize())
  }
})
</script>

<template>
  <div class="meter-page">
    <div class="page-header">
      <h2>水电与抄表管理</h2>
    </div>

    <!-- 数据统计 -->
    <el-card class="chart-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>近半年水电收支与损耗趋势</span>
        </div>
      </template>
      <!-- 修复：必须给固定的高度 -->
      <div ref="chartRef" style="width: 100%; height: 300px;"></div>
    </el-card>

    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 左侧：房间列表 -->
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <span>选择房间进行拍照</span>
          </template>
          <div class="room-list">
            <div 
              v-for="r in rooms" 
              :key="r.room_id"
              :class="['room-item', r.room_status === 'VACANT' ? 'vacant' : '']"
              @click="triggerUpload(r)"
            >
              <div class="room-info">
                <span class="room-name">{{ r.room_number }}</span>
                <span class="room-status">{{ r.room_status === 'OCCUPIED' ? '已租' : '空置' }}</span>
              </div>
              <el-upload
                v-if="r.room_status === 'OCCUPIED'"
                action="#"
                :show-file-list="false"
                :http-request="(opt) => { selectedRoom = r; handleFileUpload(opt) }"
              >
                <el-button type="primary" size="small" icon="Camera">拍照</el-button>
              </el-upload>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：识别记录 -->
      <el-col :span="18">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>AI 识别记录</span>
              <el-button type="success" size="small" :loading="loading">模拟一键连拍</el-button>
            </div>
          </template>
          
          <el-table :data="readings" style="width: 100%" stripe>
            <el-table-column prop="created_at" label="时间" width="120" />
            <el-table-column prop="room_number" label="房间" width="100" />
            <el-table-column prop="value" label="识别值" width="120" />
            <el-table-column prop="confidence" label="置信度" width="120">
              <template #default="scope">{{ (scope.row.confidence * 100).toFixed(1) }}%</template>
            </el-table-column>
            <el-table-column label="状态" width="120">
              <template #default="scope">
                <el-tag v-if="scope.row.status === 'SUCCESS'" type="success">正常</el-tag>
                <el-tag v-else-if="scope.row.status === 'ANOMALY'" type="danger">读数倒挂</el-tag>
                <el-tag v-else type="warning">人工修正</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作">
              <template #default="scope">
                <el-button 
                  v-if="scope.row.status === 'ANOMALY'" 
                  type="danger" 
                  size="small" 
                  @click="correctReading(scope.row)"
                >
                  去修正
                </el-button>
                <span v-else-if="scope.row.status === 'MANUALLY_CORRECTED'" style="color: #909399;">已修正</span>
                <span v-else style="color: #67C23A;">已入库</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.meter-page { padding: 20px; }
.page-header { margin-bottom: 20px; }
.chart-card { margin-bottom: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }

.room-list { display: flex; flex-direction: column; gap: 10px; }
.room-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px; border: 1px solid #ebeef5; border-radius: 4px;
  transition: all 0.3s;
}
.room-item:hover { background-color: #f5f7fa; }
.room-item.vacant { opacity: 0.6; background-color: #fafafa; }

.room-info { display: flex; flex-direction: column; gap: 4px; }
.room-name { font-size: 16px; font-weight: bold; }
.room-status { font-size: 12px; color: #909399; }
</style>