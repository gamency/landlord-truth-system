<script setup lang="ts">
// 这里暂时不需要逻辑
import AgentChat from './components/AgentChat.vue'
</script>

<template>
  <div class="app-layout">
    <!-- 左侧导航 -->
    <aside class="sidebar">
      <h2>房东真相</h2>
      <nav>
        <RouterLink to="/property" class="nav-item">🏢 房源管理</RouterLink>
        <RouterLink to="/billing" class="nav-item">📄 账单管理</RouterLink>
        <a class="nav-item disabled">📊 对账管理 (待开发)</a>
      </nav>
    </aside>

    <!-- 右侧内容区 -->
    <main class="main-content">
      <RouterView />
    </main>
    <!-- 新增 AI 助手 -->
    <AgentChat />
  </div>
</template>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: sans-serif; background-color: #f5f7fa; color: #333; }
.app-layout { display: flex; height: 100vh; }
.sidebar {
  width: 220px; background: #fff; border-right: 1px solid #e5e6eb;
  padding: 20px 0; display: flex; flex-direction: column;
}
.sidebar h2 { padding: 0 20px 20px; font-size: 20px; color: #1677ff; }
.nav-item {
  display: block; padding: 12px 20px; color: #4e5969; text-decoration: none;
  cursor: pointer; transition: background 0.2s;
}
.nav-item:hover, .nav-item.router-link-active { background: #e8f3ff; color: #1677ff; font-weight: bold; }
.nav-item.disabled { color: #c9cdd4; cursor: not-allowed; }
.main-content { flex: 1; padding: 24px; overflow-y: auto; }
</style>