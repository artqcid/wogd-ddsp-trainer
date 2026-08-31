<template>
  <nav class="sidebar">
    <div class="sidebar-brand">wogd-ddsp-trainer</div>

    <div class="sidebar-group">
      <div class="sidebar-group-label">Datasets &amp; Preprocessing</div>
      <ul class="sidebar-links">
        <li>
          <RouterLink to="/datasets" class="sidebar-link">Upload &amp; Ingestion</RouterLink>
        </li>
        <li>
          <RouterLink to="/datasets/manager" class="sidebar-link">Dataset Manager</RouterLink>
        </li>
        <li>
          <RouterLink to="/datasets/preprocess" class="sidebar-link">Preprocessing</RouterLink>
        </li>
      </ul>
    </div>

    <div class="sidebar-group">
      <div class="sidebar-group-label">Model Architecture</div>
      <ul class="sidebar-links">
        <li>
          <RouterLink to="/model" class="sidebar-link">Training Config</RouterLink>
        </li>
      </ul>
    </div>

    <div class="sidebar-group">
      <div class="sidebar-group-label">Training &amp; Monitor</div>
      <ul class="sidebar-links">
        <li>
          <RouterLink to="/training" class="sidebar-link">Training Dashboard</RouterLink>
        </li>
      </ul>
    </div>

    <div class="sidebar-group">
      <div class="sidebar-group-label">Inference &amp; Export</div>
      <ul class="sidebar-links">
        <li>
          <RouterLink to="/inference" class="sidebar-link">Inference Playground</RouterLink>
        </li>
        <li>
          <RouterLink to="/export" class="sidebar-link">Model Export</RouterLink>
        </li>
        <li>
          <RouterLink to="/presets" class="sidebar-link">Presets</RouterLink>
        </li>
      </ul>
    </div>
  </nav>
</template>

<script setup>
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
</script>

<style scoped>
.sidebar {
  height: 100vh;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.sidebar-brand {
  padding: 1rem;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border);
}

.sidebar-group {
  padding: 0.5rem 0;
}

.sidebar-group-label {
  padding: 0.25rem 1rem;
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-secondary);
}

.sidebar-links {
  list-style: none;
  margin: 0;
  padding: 0;
}

.sidebar-link {
  display: block;
  padding: 0.5rem 1rem;
  color: var(--text-primary);
  text-decoration: none;
  font-size: 0.875rem;
  border-left: 3px solid transparent;
  transition: background 0.15s, border-color 0.15s;
}

.sidebar-link:hover {
  background: var(--bg-tertiary);
}

.sidebar-link.router-link-active {
  background: var(--bg-tertiary);
  border-left-color: var(--accent);
  color: var(--accent);
}
</style>
