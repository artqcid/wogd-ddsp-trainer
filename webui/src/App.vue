<script setup>
import HealthView from './views/HealthView.vue'
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <h1>wogd-ddsp-trainer</h1>
    </header>
    <main class="app-main">
      <HealthView />
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
.app-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #ccc;
}
.app-main {
  flex: 1;
  padding: 1.5rem;
}
</style>
