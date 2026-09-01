<template>
  <div
    class="tier-card"
    :class="{ 'tier-card--selected': selected, 'tier-card--disabled': disabled }"
    :data-testid="`tier-card-${tier}`"
    @click="!disabled && $emit('select', tier)"
  >
    <div class="tier-card-icon" v-html="icon"></div>
    <div class="tier-card-body">
      <div class="tier-card-label">{{ label }}</div>
      <div class="tier-card-desc">{{ description }}</div>
      <div class="tier-card-feasibility" v-if="feasibility">
        <span v-if="feasibility.fits" class="badge badge--success" data-testid="fits-badge">
          ✓ fits {{ feasibility.estimated_gb }} GB
        </span>
        <span v-else class="badge badge--warning" data-testid="warning-badge">
          ⚠ needs {{ feasibility.estimated_gb }} GB
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  tier: { type: String, required: true },
  label: { type: String, required: true },
  description: { type: String, default: '' },
  icon: { type: String, default: '●' },
  feasibility: { type: Object, default: null },
  selected: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})

defineEmits(['select'])
</script>

<style scoped>
.tier-card {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--bg-secondary);
  border: 2px solid var(--border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}
.tier-card:hover {
  border-color: var(--text-muted);
}
.tier-card--selected {
  border-color: var(--accent);
  box-shadow: var(--shadow-glow);
}
.tier-card--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.tier-card-icon {
  font-size: 1.5rem;
  line-height: 1;
  flex-shrink: 0;
}
.tier-card-body {
  flex: 1;
}
.tier-card-label {
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: var(--space-1);
}
.tier-card-desc {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-bottom: var(--space-2);
}
.tier-card-feasibility {
  margin-top: var(--space-1);
}
</style>