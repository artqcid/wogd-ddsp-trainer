<script setup>
import { inject } from 'vue'

const apiClient = inject('apiClient')
</script>

<template>
  <section class="health-view">
    <h2>Health check</h2>
    <p>This scaffold view renders through the API-client abstraction.</p>
    <p data-testid="api-client-status">
      {{ apiClient ? 'API client injected' : 'API client missing' }}
    </p>
  </section>
</template>
