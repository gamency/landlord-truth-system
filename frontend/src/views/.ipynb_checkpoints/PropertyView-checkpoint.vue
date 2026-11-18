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

// ... 保留之前的代码 ...
const showRoomModal = ref(false)
const currentRoom = ref<any>(null)
const roomMeters = ref<any[]>([])

// 打开房间详情
const openRoomDetail = async (room: any) => {
  currentRoom.value = room
  showRoomModal.value = true
  await fetchRoomMeters()
}

// 获取房间的表计
const fetchRoomMeters = async () => {
  if (!currentRoom.value) return
  const res = await axios.get(`/api/v1/property/rooms/${currentRoom.value.room_id}`)
  roomMeters.value = res.data.data.meters
}

// 绑定表计
const handleBindMeter = async (type: string, label: string) => {
  const meterNumber = prompt(`请输入${label}表号（如 E001）：`)
  if (!meterNumber) return
  const reading = prompt(`请输入${label}初始读数（如 0）：`, '0')
  if (reading === null) return

  try {
    await axios.post(`/api/v1/property/rooms/${currentRoom.value.room_id}/meters`, {
      meter_type: type,
      meter_number: meterNumber,
      initial_reading: parseFloat(reading)
    })
    alert('绑定成功')
    await fetchRoomMeters()
  } catch (e: any) {
    alert(e.response?.data?.message || '绑定失败')
  }
}

// ... 保留之前的代码 ...

const showBatchModal = ref(false)
// 默认给一个 1 楼商铺、2楼出租房的模板
const batchForm = ref({
  property_name: '',
  address: '',
  floors: [
    { floor_number: 1, room_count: 2, room_type: 'SHOP', has_electric: true, has_cold_water: true, has_hot_water: false },
    { floor_number: 2, room_count: 6, room_type: 'RENTAL', has_electric: true, has_cold_water: true, has_hot_water: true }
  ]
})

const addFloorRow = () => {
  const nextFloor = batchForm.value.floors.length > 0 
    ? Math.max(...batchForm.value.floors.map(f => f.floor_number)) + 1 
    : 1
  batchForm.value.floors.push({
    floor_number: nextFloor, room_count: 1, room_type: 'RENTAL', 
    has_electric: true, has_cold_water: true, has_hot_water: true
  })
}

const removeFloorRow = (index: number) => {
  batchForm.value.floors.splice(index, 1)
}

const submitBatch = async () => {
  if (!batchForm.value.property_name || !batchForm.value.address) {
    return alert('请填写楼栋名称和地址')
  }
  if (batchForm.value.floors.length === 0) {
    return alert('至少需要配置一层楼')
  }
  
  try {
    await axios.post('/api/v1/property/properties/batch', batchForm.value)
    alert('批量生成成功！')
    showBatchModal.value = false
    fetchProperties()
  } catch (e: any) {
    alert('生成失败：' + (e.response?.data?.message || e.message))
  }
}

</script>

<template>
  <div>
    <div class="page-header">
      <h1>房源管理</h1>
      <div>
        <button class="btn-secondary" @click="handleCreateProperty">单栋添加</button>
        <button class="btn-primary" style="margin-left: 10px;" @click="showBatchModal = true">🚀 一键生成楼栋</button>
      </div>
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
            @click="openRoomDetail(room)"
            style="cursor: pointer;"
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

    <!-- 新增：房间详情弹窗 (Modal) -->
    <div v-if="showRoomModal" class="modal-overlay" @click.self="showRoomModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ currentRoom?.room_name || currentRoom?.room_number }} - 详情配置</h3>
          <button class="close-btn" @click="showRoomModal = false">×</button>
        </div>
        
        <div class="modal-body">
          <h4>📊 表计绑定情况</h4>
          <p style="font-size: 14px; color: #86909c; margin-bottom: 16px;">
            抄表前必须先绑定表计。
          </p>

          <div class="meter-list">
            <!-- 电表 -->
            <div class="meter-item">
              <span>💡 电表</span>
              <template v-if="roomMeters.find(m => m.meter_type === 'ELECTRIC')">
                <span class="bound-text">已绑定: {{ roomMeters.find(m => m.meter_type === 'ELECTRIC').meter_number }}</span>
              </template>
              <button v-else class="btn-small" @click="handleBindMeter('ELECTRIC', '电')">+ 绑定电表</button>
            </div>
            
            <!-- 冷水表 -->
            <div class="meter-item">
              <span>💧 冷水表</span>
              <template v-if="roomMeters.find(m => m.meter_type === 'COLD_WATER')">
                <span class="bound-text">已绑定: {{ roomMeters.find(m => m.meter_type === 'COLD_WATER').meter_number }}</span>
              </template>
              <button v-else class="btn-small" @click="handleBindMeter('COLD_WATER', '冷水')">+ 绑定冷水表</button>
            </div>

            <!-- 热水表 -->
            <div class="meter-item">
              <span>🔥 热水表</span>
              <template v-if="roomMeters.find(m => m.meter_type === 'HOT_WATER')">
                <span class="bound-text">已绑定: {{ roomMeters.find(m => m.meter_type === 'HOT_WATER').meter_number }}</span>
              </template>
              <button v-else class="btn-small" @click="handleBindMeter('HOT_WATER', '热水')">+ 绑定热水表</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
    <!-- 批量生成向导弹窗 -->
    <div v-if="showBatchModal" class="modal-overlay" @click.self="showBatchModal = false">
      <div class="modal-content" style="width: 650px;">
        <div class="modal-header">
          <h3>🚀 一键批量生成房源</h3>
          <button class="close-btn" @click="showBatchModal = false">×</button>
        </div>
        
        <div class="modal-body">
          <div class="form-group">
            <label>楼栋名称：</label>
            <input v-model="batchForm.property_name" type="text" placeholder="如：幸福小区2栋" class="input-text" />
            <label style="margin-left: 20px;">楼栋地址：</label>
            <input v-model="batchForm.address" type="text" placeholder="如：XX县XX路XX号" class="input-text" style="width: 200px;" />
          </div>

          <h4 style="margin-top: 24px; margin-bottom: 12px;">楼层与房间结构配置</h4>
          <table class="batch-table">
            <thead>
              <tr>
                <th>楼层</th>
                <th>房间数</th>
                <th>房间类型</th>
                <th>包含表计</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(floor, index) in batchForm.floors" :key="index">
                <td>
                  <input v-model.number="floor.floor_number" type="number" class="input-small" /> 楼
                </td>
                <td>
                  <input v-model.number="floor.room_count" type="number" class="input-small" /> 间
                </td>
                <td>
                  <select v-model="floor.room_type" class="input-small">
                    <option value="RENTAL">出租房</option>
                    <option value="SHOP">商铺</option>
                    <option value="SELF_USE">自住</option>
                  </select>
                </td>
                <td>
                  <label><input type="checkbox" v-model="floor.has_electric" /> 💡电</label>
                  <label><input type="checkbox" v-model="floor.has_cold_water" /> 💧冷水</label>
                  <label><input type="checkbox" v-model="floor.has_hot_water" /> 🔥热水</label>
                </td>
                <td>
                  <button @click="removeFloorRow(index)" class="text-red">删除</button>
                </td>
              </tr>
            </tbody>
          </table>
          <button class="btn-secondary" style="margin-top: 12px; font-size: 12px;" @click="addFloorRow">+ 增加楼层</button>

          <div class="modal-footer">
            <button class="btn-primary" @click="submitBatch">确认生成结构</button>
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

/* ... 保留之前的样式 ... */

/* 弹窗样式 */
.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.modal-content {
  background: white; width: 400px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  overflow: hidden;
}
.modal-header {
  padding: 16px 20px; border-bottom: 1px solid #e5e6eb; display: flex; justify-content: space-between; align-items: center;
}
.modal-header h3 { font-size: 18px; margin: 0; }
.close-btn { background: none; border: none; font-size: 24px; color: #86909c; cursor: pointer; }
.modal-body { padding: 20px; }
.meter-list { display: flex; flex-direction: column; gap: 12px; }
.meter-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px; border: 1px solid #e5e6eb; border-radius: 6px;
}
.btn-small { background: #e8f3ff; color: #1677ff; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 13px; }
.btn-small:hover { background: #1677ff; color: white; }
.bound-text { color: #00b42a; font-size: 14px; font-weight: bold; }

.btn-secondary { background: white; border: 1px solid #1677ff; color: #1677ff; padding: 10px 16px; border-radius: 4px; cursor: pointer; }
.form-group { display: flex; align-items: center; margin-bottom: 20px; }
.input-text { border: 1px solid #e5e6eb; padding: 8px; border-radius: 4px; margin-left: 10px; }
.batch-table { width: 100%; border-collapse: collapse; text-align: left; }
.batch-table th, .batch-table td { padding: 12px 8px; border-bottom: 1px solid #e5e6eb; font-size: 14px; }
.input-small { border: 1px solid #e5e6eb; padding: 4px 8px; border-radius: 4px; width: 60px; }
.batch-table label { margin-right: 8px; font-size: 13px; cursor: pointer; }
.text-red { color: #f53f3f; background: none; border: none; cursor: pointer; }
.modal-footer { margin-top: 24px; text-align: right; border-top: 1px solid #e5e6eb; padding-top: 16px; }
</style>