<script setup>
import { computed } from 'vue'

const props = defineProps({
  confidence: {
    type: Number,
    default: 0
  }
})

const level = computed(() => {
  if (props.confidence >= 0.8) return 'high'
  if (props.confidence >= 0.5) return 'medium'
  return 'low'
})

const label = computed(() => `Confidence: ${Math.round(props.confidence * 100)}%`)
</script>

<template>
  <div class="pitch-indicator">
    <div class="pitch-bar" data-testid="pitch-bar">
      <div
        class="pitch-bar-fill"
        :class="level"
        :style="{ width: `${Math.min(Math.max(props.confidence, 0), 1) * 100}%` }"
      ></div>
    </div>
    <span class="pitch-label" data-testid="pitch-label">{{ label }}</span>
  </div>
</template>

<style scoped>
.pitch-indicator { display: flex; align-items: center; gap: 0.75rem; margin-top: 0.75rem; }
.pitch-bar { width: 200px; height: 12px; background: var(--bg-tertiary); border-radius: 6px; overflow: hidden; }
.pitch-bar-fill { height: 100%; border-radius: 6px; transition: width 0.3s; }
.pitch-bar-fill.high { background: var(--success); }
.pitch-bar-fill.medium { background: var(--warning); }
.pitch-bar-fill.low { background: var(--error); }
.pitch-label { font-size: 0.75rem; color: var(--text-secondary); }
</style>
