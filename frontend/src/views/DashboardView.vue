<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const summary = ref({ total: 0, occupied: 0, vacant: 0, total_unpaid: 0 })
const floors = ref<any[]>([])
const loading = ref(false)

const fetchDashboard = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/v1/property/dashboard')
    summary.value = res.data.data.summary
    floors.value = res.data.data.floors
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchDashboard)
</script>

<template>
  <div>
    <div class="page-header">
      <h1>经营看板</h1>
      <button class="btn-secondary" @click="fetchDashboard">🔄 刷新数据</button>
    </div>

    <!-- 顶部汇总卡片 -->
    <div class="summary-cards">
      <div class="card">
        <div class="title">总房间数</div>
        <div class="value">{{ summary.total }} <span>间</span></div>
      </div>
      <div class="card">
        <div class="title">在租房间</div>
        <div class="value" style="color: #00b42a;">{{ summary.occupied }} <span>间</span></div>
      </div>
      <div class="card">
        <div class="title">空置房间</div>
        <div class="value" style="color: #86909c;">{{ summary.vacant }} <span>间</span></div>
      </div>
      <div class="card">
        <div class="title">总欠款</div>
        <div class="value" style="color: #f53f3f;">¥{{ summary.total_unpaid.toFixed(2) }}</div>
      </div>
    </div>

    <!-- 楼层空间图 -->
    <div class="dashboard-container">
      <div v-if="loading" class="empty">数据加载中...</div>
      <div v-else-if="floors.length === 0" class="empty">暂无房间数据，请先去“房源管理”建房。</div>
      
      <div v-else class="floor-list">
        <div v-for="floor in floors" :key="floor.floor_number" class="floor-row">
          <div class="floor-label">{{ floor.floor_number }}F</div>
          
          <div class="rooms-grid">
            <div 
              v-for="room in floor.rooms" 
              :key="room.room_id"
              :class="['room-card', 
                room.status === 'VACANT' ? 'vacant' : 
                (room.unpaid > 0 ? 'danger' : 'occupied')
              ]"
            >
              <div class="room-num">{{ room.room_number }}</div>
              
              <template v-if="room.status === 'VACANT'">
                <div class="room-status">空置</div>
              </template>
              
              <template v-else>
                <div class="tenant">{{ room.tenant_name || '已租' }}</div>
                <div v-if="room.unpaid > 0" class="unpaid">
                  欠 ¥{{ room.unpaid.toFixed(0) }}
                </div>
                <div v-else class="paid">已结清</div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.btn-secondary { background: white; border: 1px solid #e5e6eb; padding: 8px 16px; border-radius: 4px; cursor: pointer; }

/* 顶部汇总卡片 */
.summary-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.card .title { color: #86909c; font-size: 14px; margin-bottom: 8px; }
.card .value { font-size: 28px; font-weight: bold; color: #1d2129; }
.card .value span { font-size: 14px; font-weight: normal; color: #86909c; }

/* 楼层看板 */
.dashboard-container { background: white; padding: 24px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); min-height: 400px; }
.floor-list { display: flex; flex-direction: column; gap: 20px; }
.floor-row { display: flex; align-items: stretch; gap: 20px; border-bottom: 1px dashed #f2f3f5; padding-bottom: 20px; }
.floor-row:last-child { border-bottom: none; }
.floor-label { width: 50px; display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: bold; color: #4e5969; background: #f7f8fa; border-radius: 8px; }

.rooms-grid { display: flex; flex-wrap: wrap; gap: 16px; flex: 1; }
.room-card { width: 120px; height: 90px; border-radius: 8px; padding: 12px; display: flex; flex-direction: column; border: 2px solid transparent; transition: transform 0.2s; cursor: pointer; }
.room-card:hover { transform: translateY(-2px); }

/* 状态颜色 */
.room-card.vacant { background: #f7f8fa; border-color: #e5e6eb; color: #86909c; }
.room-card.occupied { background: #e8ffea; border-color: #00b42a; color: #1d2129; }
.room-card.danger { background: #fffafa; border-color: #f53f3f; color: #1d2129; }

.room-num { font-size: 18px; font-weight: bold; margin-bottom: auto; }
.room-status { font-size: 14px; }
.tenant { font-size: 13px; color: #4e5969; margin-bottom: 4px; }
.unpaid { font-size: 14px; font-weight: bold; color: #f53f3f; }
.paid { font-size: 12px; color: #00b42a; }
.empty { text-align: center; color: #86909c; margin-top: 100px; }
</style>