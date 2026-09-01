<template>
  <div class="feasibility-banner" :class="bannerClass" data-testid="feasibility-banner">
    <template v-if="noGpu">
      <span class="banner-icon">⚠️</span>
      <span data-testid="no-gpu-text">No GPU detected — training will run on CPU (slow).</span>
    </template>
    <template v-else-if="feasibility">
      <span class="banner-icon" v-if="feasibility.fits">✓</span>
      <span class="banner-icon" v-else>⚠</span>
      <span>
        GPU · {{ availableGb }} GB available ·
        current config ~{{ feasibility.estimated_gb }} GB
        <span v-if="feasibility.fits" class="banner-ok">✓</span>
        <span v-else class="banner-warn">{{ feasibility.warning }}</span>
      </span>
    </template>
    <span v-else class="banner-loading">Loading GPU info...</span>
  </div>
</template>

<script setup>
import { computed, inject, onMounted, watch } from 'vue'
import { useModelConfigStore } from '../stores/modelConfig.js'

const store = useModelConfigStore()
const apiClient = inject('apiClient')

const props = defineProps({
  availableGb: { type: Number, default: 0 },
})

const noGpu = computed(() => {
  return !store.gpuFeasibility?.available_gb && store.gpuFeasibility?.available_gb !== 0
})

const feasibility = computed(() => {
  return store.gpuFeasibility
})

const bannerClass = computed(() => {
  if (!feasibility.value) return 'banner--loading'
  if (noGpu.value) return 'banner--warn'
  return feasibility.value.fits ? 'banner--ok' : 'banner--warn'
})

async function refresh() {
  if (apiClient) {
    await store.checkFeasibility(apiClient)
  }
}

watch(() => store.activeTier, refresh)
watch(() => store.advancedParams.n_voices, refresh)
watch(() => store.advancedParams.use_latent, refresh)
watch(() => store.advancedParams.use_content_encoder, refresh)

onMounted(refresh)
</script>

<style scoped>
.feasibility-banner {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  margin-bottom: var(--space-4);
}
.banner--ok {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid var(--tier-standard);
  color: var(--success);
}
.banner--warn {
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid var(--tier-hacks);
  color: var(--warning);
}
.banner--loading {
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  color: var(--text-secondary);
}
.banner-icon {
  font-weight: 700;
  font-size: 1rem;
}
.banner-ok { color: var(--success); }
.banner-warn { color: var(--warning); }
.banner-loading { color: var(--text-muted); }
</style>