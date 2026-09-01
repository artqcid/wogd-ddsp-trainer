<template>
  <header class="topbar">
    <div class="topbar-brand">
      wogd-ddsp-trainer
      <span v-if="version" class="topbar-version">{{ version }}</span>
      <span v-else class="topbar-version">loading…</span>
    </div>

    <div class="topbar-center">
      <span v-if="activeTierLabel" class="tier-pill" :style="{ background: tierColor(store.activeTier) + '22', color: tierColor(store.activeTier), borderColor: tierColor(store.activeTier) }" data-testid="tier-badge">
        {{ tierIcon(store.activeTier) }} {{ activeTierLabel }}
      </span>
    </div>

    <div class="topbar-status">
      <span>
        <span :class="['status-dot', healthStatus]"></span>
        {{ healthLabel }}
      </span>
      <span>
        <span :class="['status-dot', tbStatus]"></span>
        {{ tbLabel }}
      </span>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, inject, onMounted } from 'vue'
import { useModelConfigStore } from '../stores/modelConfig.js'
import { tierLabel, tierColor, tierIcon } from '../utils/tierColors.js'

const store = useModelConfigStore()
const apiClient = inject('apiClient')
const version = ref(null)
const healthOk = ref(null)
const tbRunning = ref(null)
const healthStatus = ref('err')
const healthLabel = ref('Backend: unknown')
const tbStatus = ref('warn')
const tbLabel = ref('TensorBoard: unknown')

const activeTierLabel = computed(() => {
  if (!store.activeTier) return null
  return tierLabel(store.activeTier)
})

onMounted(async () => {
  if (!apiClient) return

  try {
    const health = await apiClient.health()
    version.value = health.version || null
    healthOk.value = health.ok
    healthStatus.value = healthOk.value ? 'ok' : 'err'
    healthLabel.value = healthOk.value ? 'Backend: ok' : 'Backend: error'
  } catch {
    healthStatus.value = 'err'
    healthLabel.value = 'Backend: unreachable'
  }

  try {
    const tb = await apiClient.getTensorboard()
    tbRunning.value = tb.running
    tbStatus.value = tb.running ? 'ok' : 'warn'
    tbLabel.value = tb.running ? 'TensorBoard: running' : 'TensorBoard: stopped'
  } catch {
    tbStatus.value = 'warn'
    tbLabel.value = 'TensorBoard: unknown'
  }
})
</script>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1rem;
  height: 100%;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
}
.topbar-brand {
  font-weight: 600;
  font-size: 0.875rem;
}
.topbar-version {
  margin-left: 0.5rem;
  font-size: 0.75rem;
  color: var(--text-secondary);
}
.topbar-center {
  display: flex;
  align-items: center;
}
.tier-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 2px 0.75rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  border: 1px solid;
}
.topbar-status {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 0.75rem;
  color: var(--text-secondary);
}
.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 0.25rem;
}
.status-dot.ok { background: var(--success); }
.status-dot.warn { background: var(--warning); }
.status-dot.err { background: var(--error); }
</style>