<script setup lang="ts">
import { ref, nextTick } from 'vue'

const isOpen = ref(false)
const inputText = ref('')
const chatHistory = ref<{role: string, content: string, traces?: string[]}[]>([])
const isGenerating = ref(false)
const chatBody = ref<HTMLElement | null>(null)

const toggleChat = () => {
  isOpen.value = !isOpen.value
}

const scrollToBottom = async () => {
  await nextTick()
  if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight
}

const sendMessage = async () => {
  if (!inputText.value.trim() || isGenerating.value) return
  
  const userMsg = inputText.value
  inputText.value = ''
  chatHistory.value.push({ role: 'user', content: userMsg })
  scrollToBottom()
  
  isGenerating.value = true
  const aiMsg = { role: 'ai', content: '', traces: [] as string[] }
  chatHistory.value.push(aiMsg)
  
  try {
    const response = await fetch('/api/v1/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userMsg })
    })

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    
    while (true) {
      const { done, value } = await reader!.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          
          if (data.event === 'trace') {
            // 如果存在思考过程，加到 traces 数组
            aiMsg.traces?.push(data.text)
          } else if (data.event === 'message') {
            // 打印文字
            aiMsg.content += data.text
          }
          scrollToBottom()
        }
      }
    }
  } catch (e) {
    aiMsg.content = '网络出小差了，请稍后再试。'
  } finally {
    isGenerating.value = false
    scrollToBottom()
  }
}
</script>

<template>
  <div class="agent-wrapper">
    <!-- 对话面板 -->
    <div v-if="isOpen" class="chat-panel">
      <div class="chat-header">
        <span>✨ AI 经营助手</span>
        <button class="close-btn" @click="toggleChat">×</button>
      </div>
      
      <div class="chat-body" ref="chatBody">
        <div v-if="chatHistory.length === 0" class="empty-hint">
          老板您好！我是您的智能管家。<br>
          您可以直接问我：<br>
          <span style="color: #1677ff; cursor: pointer;" @click="inputText = '谁还欠钱？'">"谁还欠钱？"</span>
        </div>

        <div v-for="(msg, idx) in chatHistory" :key="idx" :class="['message', msg.role]">
          <!-- AI 思考轨迹 -->
          <div v-if="msg.traces && msg.traces.length > 0" class="trace-box">
            <div v-for="(trace, tIdx) in msg.traces" :key="tIdx" class="trace-item">{{ trace }}</div>
          </div>
          <!-- 气泡内容 -->
          <div v-if="msg.content" class="bubble" style="white-space: pre-wrap;">{{ msg.content }}</div>
        </div>
      </div>

      <div class="chat-input-area">
        <input 
          v-model="inputText" 
          @keyup.enter="sendMessage"
          type="text" 
          placeholder="输入您的问题..." 
          :disabled="isGenerating"
        />
        <button @click="sendMessage" :disabled="isGenerating">
          {{ isGenerating ? '思考中' : '发送' }}
        </button>
      </div>
    </div>

    <!-- 悬浮球 -->
    <div class="floating-ball" @click="toggleChat">
      ✨
    </div>
  </div>
</template>

<style scoped>
.agent-wrapper { position: fixed; bottom: 30px; right: 30px; z-index: 9999; font-family: sans-serif; }

/* 悬浮球 */
.floating-ball {
  width: 56px; height: 56px; border-radius: 50%;
  background: linear-gradient(135deg, #1677ff, #00b4ff);
  color: white; font-size: 24px; display: flex; align-items: center; justify-content: center;
  cursor: pointer; box-shadow: 0 4px 12px rgba(22,119,255,0.4);
  transition: transform 0.2s;
}
.floating-ball:hover { transform: scale(1.1); }

/* 对话面板 */
.chat-panel {
  position: absolute; bottom: 70px; right: 0;
  width: 380px; height: 550px; background: white;
  border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.15);
  display: flex; flex-direction: column; overflow: hidden;
  border: 1px solid #e5e6eb;
}
.chat-header {
  padding: 16px; background: #f7f8fa; border-bottom: 1px solid #e5e6eb;
  display: flex; justify-content: space-between; font-weight: bold; color: #1d2129;
}
.close-btn { background: none; border: none; font-size: 20px; cursor: pointer; color: #86909c; }

.chat-body { flex: 1; padding: 16px; overflow-y: auto; background: #fafafa; }
.empty-hint { color: #86909c; font-size: 14px; text-align: center; margin-top: 50px; line-height: 1.6; }

.message { margin-bottom: 16px; display: flex; flex-direction: column; }
.message.user { align-items: flex-end; }
.message.ai { align-items: flex-start; }

.bubble {
  max-width: 85%; padding: 10px 14px; border-radius: 8px; font-size: 14px; line-height: 1.5;
}
.message.user .bubble { background: #1677ff; color: white; border-top-right-radius: 0; }
.message.ai .bubble { background: white; color: #1d2129; border: 1px solid #e5e6eb; border-top-left-radius: 0; }

/* 思考轨迹 */
.trace-box {
  background: #f2f3f5; border-radius: 6px; padding: 8px 12px; margin-bottom: 8px;
  font-size: 12px; color: #4e5969; width: 90%;
}
.trace-item { margin-bottom: 4px; }

/* 输入区 */
.chat-input-area { padding: 12px; background: white; border-top: 1px solid #e5e6eb; display: flex; gap: 8px; }
.chat-input-area input { flex: 1; border: 1px solid #e5e6eb; border-radius: 20px; padding: 0 16px; outline: none; }
.chat-input-area button { background: #1677ff; color: white; border: none; border-radius: 20px; padding: 0 16px; cursor: pointer; }
.chat-input-area button:disabled { background: #c9cdd4; }
</style>