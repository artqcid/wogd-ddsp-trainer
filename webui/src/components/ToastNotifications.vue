<template>
  <TransitionGroup name="toast" tag="div" class="toast-container">
    <div v-for="item in store.items" :key="item.id" class="toast" :class="item.kind" data-testid="toast">
      <span class="toast-message">{{ item.message }}</span>
      <button class="toast-close" @click="store.dismiss(item.id)">&times;</button>
    </div>
  </TransitionGroup>
</template>

<script setup>
import { useNotificationsStore } from '../stores/notifications.js'

const store = useNotificationsStore()
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  pointer-events: none;
}
.toast {
  pointer-events: auto;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.8rem;
  color: #000;
  max-width: 360px;
  display: flex;
  gap: 0.75rem;
  align-items: center;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
.toast.info { background: var(--accent); }
.toast.success { background: var(--success); }
.toast.warn { background: var(--warning); }
.toast.error { background: var(--error); }
.toast-close { background: none; border: none; color: inherit; font-size: 1.1rem; cursor: pointer; padding: 0; line-height: 1; }
.toast-message { flex: 1; }

.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from { opacity: 0; transform: translateX(30px); }
.toast-leave-to { opacity: 0; transform: translateX(30px); }
</style>