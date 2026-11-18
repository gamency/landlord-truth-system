<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const drafts = ref<any[]>([])
const loading = ref(false)

const fetchDrafts = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/v1/property/bills/drafts')
    drafts.value = res.data.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const confirmDraft = async (draftId: string) => {
  if (!confirm('确认后将生成正式账单，是否继续？')) return
  try {
    await axios.post(`/api/v1/property/bills/drafts/${draftId}/confirm`)
    alert('确认成功！')
    fetchDrafts() // 刷新列表
  } catch (e: any) {
    alert('确认失败')
  }
}

onMounted(fetchDrafts)
</script>

<template>
  <div>
    <div class="page-header">
      <h1>账单草稿确认</h1>
    </div>

    <div class="card-container">
      <div v-if="loading" class="empty-text">加载中...</div>
      <div v-else-if="drafts.length === 0" class="empty-text">
        🎉 太棒了，当前没有待确认的账单草稿。
      </div>
      
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>房间号</th>
            <th>账单金额</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="draft in drafts" :key="draft.draft_id">
            <td><strong>{{ draft.room_number }}</strong></td>
            <td style="color: #f53f3f; font-weight: bold;">¥{{ draft.amount.toFixed(2) }}</td>
            <td><span class="badge warning">待确认</span></td>
            <td>
              <button class="btn-primary" style="padding: 6px 12px; font-size: 13px;" @click="confirmDraft(draft.draft_id)">
                确认账单
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.page-header { margin-bottom: 20px; }
.card-container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.empty-text { text-align: center; color: #86909c; padding: 40px 0; }
.data-table { width: 100%; border-collapse: collapse; text-align: left; }
.data-table th, .data-table td { padding: 12px 16px; border-bottom: 1px solid #e5e6eb; }
.data-table th { background: #f7f8fa; color: #4e5969; font-weight: 500; }
.badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
.badge.warning { background: #fff7e8; color: #ff7d00; }
</style>