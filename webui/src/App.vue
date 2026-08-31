<script setup>
import { RouterView } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import ToastNotifications from './components/ToastNotifications.vue'
import TopBar from './components/TopBar.vue'
</script>

<template>
  <ToastNotifications />
  <div class="app-shell">
    <Sidebar class="app-sidebar" />
    <div class="app-main">
      <TopBar class="app-topbar" />
      <div class="app-content">
        <RouterView />
      </div>
    </div>
  </div>
</template>

<style scoped>
:root {
  --bg-primary: #0d1117;
  --bg-secondary: #161b22;
  --bg-tertiary: #21262d;
  --text-primary: #e6edf3;
  --text-secondary: #8b949e;
  --accent: #58a6ff;
  --accent-hover: #79c0ff;
  --border: #30363d;
  --success: #3fb950;
  --warning: #d29922;
  --error: #f85149;
}

.app-shell {
  display: flex;
  min-height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
}

.app-sidebar {
  width: 200px;
  flex-shrink: 0;
}

.app-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.app-topbar {
  height: 48px;
  flex-shrink: 0;
}

.app-content {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
}
</style>
