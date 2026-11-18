<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const activeTab = ref<'drafts' | 'bills' | 'payments'>('drafts')

// ====== 草稿相关 ======
const drafts = ref<any[]>([])
const loading = ref(false)

const fetchDrafts = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/v1/property/bills/drafts')
    drafts.value = res.data.data
  } finally { loading.value = false }
}

const confirmDraft = async (draftId: string) => {
  if (!confirm('确认后将生成正式账单，是否继续？')) return
  await axios.post(`/api/v1/property/bills/drafts/${draftId}/confirm`)
  fetchDrafts()
  fetchBills()
}

// ====== 已确认账单相关 ======
const bills = ref<any[]>([])
const fetchBills = async () => {
  const res = await axios.get('/api/v1/property/bills/confirmed')
  bills.value = res.data.data
}

// ====== 收款相关 ======
const payments = ref<any[]>([])
const showPaymentModal = ref(false)
const paymentForm = ref({ amount: 0, payer_name: '', channel: 'WECHAT' })

const fetchPayments = async () => {
  const res = await axios.get('/api/v1/property/payments')
  payments.value = res.data.data
}

const submitPayment = async () => {
  if (!paymentForm.value.payer_name || paymentForm.value.amount <= 0) {
    return alert('请填写付款人和金额')
  }
  await axios.post('/api/v1/property/payments', paymentForm.value)
  showPaymentModal.value = false
  paymentForm.value = { amount: 0, payer_name: '', channel: 'WECHAT' }
  fetchPayments()
}

// ====== 核销相关 ======
const showWriteOffModal = ref(false)
const currentPayment = ref<any>(null)
const writeOffForm = ref({ bill_id: '', amount: 0 })

const openWriteOff = (payment: any) => {
  currentPayment.value = payment
  writeOffForm.value = { bill_id: '', amount: payment.remaining_amount }
  showWriteOffModal.value = true
}

const selectBill = (bill: any) => {
  writeOffForm.value.bill_id = bill.bill_id
  // 如果账单剩余 < 收款剩余，默认按账单填
  const minAmount = Math.min(bill.remaining_amount, currentPayment.value.remaining_amount)
  writeOffForm.value.amount = minAmount
}

const submitWriteOff = async () => {
  if (!writeOffForm.value.bill_id) return alert('请选择要核销的账单')
  try {
    await axios.post(`/api/v1/property/payments/${currentPayment.value.payment_id}/write-off`, writeOffForm.value)
    alert('核销成功')
    showWriteOffModal.value = false
    fetchPayments()
    fetchBills()
  } catch (e: any) {
    alert(e.response?.data?.message || '核销失败')
  }
}

onMounted(() => {
  fetchDrafts()
  fetchBills()
  fetchPayments()
})

// ... 保留之前的代码 ...

// ====== 账单直接收款 ======
const showPayModal = ref(false)
const payBillTarget = ref<any>(null)
const payForm = ref({ amount: 0, channel: 'WECHAT', payer_name: '' })

const openPayModal = (bill: any) => {
  payBillTarget.value = bill
  // 默认带出全部欠款金额
  payForm.value = { 
    amount: bill.remaining_amount, 
    channel: 'WECHAT', 
    payer_name: '' 
  }
  showPayModal.value = true
}

const submitPay = async () => {
  if (payForm.value.amount <= 0) return alert('金额必须大于0')
  try {
    await axios.post(`/api/v1/property/bills/${payBillTarget.value.bill_id}/pay`, payForm.value)
    alert('收款成功！')
    showPayModal.value = false
    fetchBills() // 刷新账单列表，这笔账单会消失
    fetchPayments() // 刷新流水
  } catch (e: any) {
    alert(e.response?.data?.message || '收款失败')
  }
}

</script>

<template>
  <div>
    <div class="page-header">
      <h1>财务管理</h1>
    </div>

    <!-- Tab 切换 -->
    <div class="tabs">
      <div :class="['tab', { active: activeTab === 'drafts' }]" @click="activeTab = 'drafts'">
        📄 待确认草稿 <span v-if="drafts.length" class="dot">{{ drafts.length }}</span>
      </div>
      <div :class="['tab', { active: activeTab === 'bills' }]" @click="activeTab = 'bills'">
        💰 未结清账单
      </div>
      <div :class="['tab', { active: activeTab === 'payments' }]" @click="activeTab = 'payments'">
        💳 收款流水
      </div>
    </div>

    <!-- Tab 1：草稿 -->
    <div v-if="activeTab === 'drafts'" class="card-container">
      <div v-if="drafts.length === 0" class="empty-text">🎉 当前没有待确认草稿</div>
      <table v-else class="data-table">
        <thead><tr><th>房间号</th><th>账单金额</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="d in drafts" :key="d.draft_id">
            <td><strong>{{ d.room_number }}</strong></td>
            <td style="color: #f53f3f; font-weight: bold;">¥{{ d.amount.toFixed(2) }}</td>
            <td><button class="btn-primary" @click="confirmDraft(d.draft_id)">确认账单</button></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Tab 2：未结清账单 -->
    <div v-if="activeTab === 'bills'" class="card-container">
      <div v-if="bills.length === 0" class="empty-text">🎉 所有账单均已结清</div>
      <table v-else class="data-table">
        <thead>
          <tr><th>房间号</th><th>账单总额</th><th>已收</th><th>欠款</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="b in bills" :key="b.bill_id">
            <td><strong>{{ b.room_number }}</strong></td>
            <td>¥{{ b.amount.toFixed(2) }}</td>
            <td style="color: #00b42a;">¥{{ b.paid_amount.toFixed(2) }}</td>
            <td style="color: #f53f3f; font-weight: bold;">¥{{ b.remaining_amount.toFixed(2) }}</td>
            <td>
              <!-- 新增：去收款按钮 -->
              <button class="btn-primary" style="background: #00b42a; padding: 4px 10px; font-size: 13px;" @click="openPayModal(b)">
                去收款
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Tab 3：收款流水 -->
    <div v-if="activeTab === 'payments'" class="card-container">
      <div style="margin-bottom: 16px;">
        <button class="btn-primary" @click="showPaymentModal = true">+ 录入收款</button>
      </div>
      <div v-if="payments.length === 0" class="empty-text">暂无收款记录</div>
      <table v-else class="data-table">
        <thead><tr><th>时间</th><th>付款人</th><th>收款金额</th><th>未核销</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="p in payments" :key="p.payment_id">
            <td>{{ p.received_at }}</td>
            <td>{{ p.payer_name }}</td>
            <td style="color: #00b42a; font-weight: bold;">¥{{ p.amount.toFixed(2) }}</td>
            <td style="color: #f53f3f;">¥{{ p.remaining_amount.toFixed(2) }}</td>
            <td><span :class="['badge', p.status === 'WRITTEN_OFF' ? 'success' : 'warning']">{{ p.status === 'WRITTEN_OFF' ? '已核销' : '待核销' }}</span></td>
            <td>
              <button v-if="p.status !== 'WRITTEN_OFF'" class="btn-primary" style="padding: 4px 10px; font-size: 13px;" @click="openWriteOff(p)">
                核销
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 录入收款弹窗 -->
    <div v-if="showPaymentModal" class="modal-overlay" @click.self="showPaymentModal = false">
      <div class="modal-content">
        <div class="modal-header"><h3>录入收款</h3><button class="close-btn" @click="showPaymentModal = false">×</button></div>
        <div class="modal-body">
          <div class="form-item"><label>付款人：</label><input v-model="paymentForm.payer_name" class="input-text" placeholder="如：郑" /></div>
          <div class="form-item"><label>金额：</label><input v-model.number="paymentForm.amount" type="number" class="input-text" /></div>
          <div class="form-item">
            <label>渠道：</label>
            <select v-model="paymentForm.channel" class="input-text">
              <option value="WECHAT">微信</option><option value="ALIPAY">支付宝</option>
              <option value="CASH">现金</option><option value="BANK">银行转账</option>
            </select>
          </div>
          <button class="btn-primary" style="width: 100%; margin-top: 12px;" @click="submitPayment">确认录入</button>
        </div>
      </div>
    </div>

    <!-- 核销弹窗 -->
    <div v-if="showWriteOffModal" class="modal-overlay" @click.self="showWriteOffModal = false">
      <div class="modal-content" style="width: 500px;">
        <div class="modal-header"><h3>核销到账单</h3><button class="close-btn" @click="showWriteOffModal = false">×</button></div>
        <div class="modal-body">
          <p style="margin-bottom: 16px; color: #4e5969;">
            当前收款剩余：<strong style="color: #00b42a;">¥{{ currentPayment?.remaining_amount.toFixed(2) }}</strong>
          </p>
          <p style="margin-bottom: 8px; font-weight: bold;">选择要核销的账单：</p>
          <div v-if="bills.length === 0" style="color: #86909c; padding: 20px 0;">暂无可核销的账单</div>
          <div v-for="b in bills" :key="b.bill_id"
               :class="['bill-choice', { selected: writeOffForm.bill_id === b.bill_id }]"
               @click="selectBill(b)">
            <div><strong>{{ b.room_number }}</strong> - 欠款 <span style="color: #f53f3f;">¥{{ b.remaining_amount.toFixed(2) }}</span></div>
          </div>
          <div class="form-item" style="margin-top: 16px;">
            <label>本次核销：</label>
            <input v-model.number="writeOffForm.amount" type="number" class="input-text" />
          </div>
          <button class="btn-primary" style="width: 100%; margin-top: 12px;" @click="submitWriteOff">确认核销</button>
        </div>
      </div>
    </div>
  </div>

    <!-- 快捷收款弹窗 -->
    <div v-if="showPayModal" class="modal-overlay" @click.self="showPayModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>收款 - {{ payBillTarget?.room_number }}</h3>
          <button class="close-btn" @click="showPayModal = false">×</button>
        </div>
        <div class="modal-body">
          <p style="margin-bottom: 16px; color: #4e5969;">
            当前欠款：<strong style="color: #f53f3f;">¥{{ payBillTarget?.remaining_amount.toFixed(2) }}</strong>
          </p>
          <div class="form-item">
            <label>实收金额：</label>
            <input v-model.number="payForm.amount" type="number" class="input-text" />
          </div>
          <div class="form-item">
            <label>付款人：</label>
            <input v-model="payForm.payer_name" class="input-text" placeholder="选填，如：郑" />
          </div>
          <div class="form-item">
            <label>渠道：</label>
            <select v-model="payForm.channel" class="input-text">
              <option value="WECHAT">微信</option><option value="ALIPAY">支付宝</option>
              <option value="CASH">现金</option><option value="BANK">银行转账</option>
            </select>
          </div>
          <button class="btn-primary" style="width: 100%; margin-top: 12px; background: #00b42a;" @click="submitPay">
            确认收款
          </button>
        </div>
      </div>
    </div>
</template>

<style scoped>
.page-header { margin-bottom: 20px; }
.tabs { display: flex; gap: 8px; margin-bottom: 16px; border-bottom: 1px solid #e5e6eb; }
.tab { padding: 12px 20px; cursor: pointer; color: #4e5969; border-bottom: 2px solid transparent; transition: 0.2s; }
.tab.active { color: #1677ff; border-bottom-color: #1677ff; font-weight: bold; }
.dot { background: #f53f3f; color: white; border-radius: 10px; padding: 1px 6px; font-size: 11px; margin-left: 6px; }
.card-container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.empty-text { text-align: center; color: #86909c; padding: 40px 0; }
.data-table { width: 100%; border-collapse: collapse; text-align: left; }
.data-table th, .data-table td { padding: 12px 16px; border-bottom: 1px solid #e5e6eb; }
.data-table th { background: #f7f8fa; color: #4e5969; font-weight: 500; }
.badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
.badge.warning { background: #fff7e8; color: #ff7d00; }
.badge.success { background: #e8ffea; color: #00b42a; }
.btn-primary { background: #1677ff; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }
.form-item { display: flex; align-items: center; margin-bottom: 12px; }
.form-item label { width: 80px; font-size: 14px; color: #4e5969; }
.input-text { flex: 1; border: 1px solid #e5e6eb; padding: 8px; border-radius: 4px; }
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-content { background: white; width: 400px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
.modal-header { padding: 16px 20px; border-bottom: 1px solid #e5e6eb; display: flex; justify-content: space-between; align-items: center; }
.close-btn { background: none; border: none; font-size: 24px; color: #86909c; cursor: pointer; }
.modal-body { padding: 20px; }
.bill-choice { padding: 12px; border: 1px solid #e5e6eb; border-radius: 6px; margin-bottom: 8px; cursor: pointer; transition: 0.2s; }
.bill-choice:hover { border-color: #1677ff; }
.bill-choice.selected { border-color: #1677ff; background: #e8f3ff; }
</style>