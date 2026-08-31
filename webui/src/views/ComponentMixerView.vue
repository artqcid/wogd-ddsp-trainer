<script setup>
import { ref, inject, onMounted } from 'vue'
import ComponentMixer from '../components/ComponentMixer.vue'

const apiClient = inject('apiClient')
const models = ref([])

onMounted(async () => {
  if (!apiClient) return
  try {
    models.value = await apiClient.listModels()
  } catch (e) {
    console.error('Failed to load models:', e)
  }
})

function onApplyConfig(config) {
  console.log('Apply mixer config:', config)
}
</script>

<template>
  <section class="mixer-view">
    <header class="view-header">
      <h2>Component Mixer</h2>
      <p class="view-description">Balance harmonics vs filtered noise for creative sound design.</p>
    </header>

    <ComponentMixer
      :n-harmonics="60"
      :n-filter-banks="32"
      :harmonic-gain="1.0"
      :noise-gain="1.0"
      @update="(v) => console.log('Mixer update:', v)"
      @apply-config="onApplyConfig"
    />
  </section>
</template>

<style scoped>
.mixer-view {
  max-width: 600px;
}
.view-header {
  margin-bottom: 1rem;
}
.view-header h2 {
  margin: 0;
  color: var(--text-primary);
}
.view-description {
  color: var(--text-secondary);
  font-size: 0.85rem;
  margin: 0.25rem 0 0 0;
}
</style>
