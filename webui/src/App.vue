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
.app-shell {
  display: flex;
  min-height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: var(--font-sans);
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
