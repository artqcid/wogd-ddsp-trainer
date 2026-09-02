<script setup>
import { inject, ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'

const apiClient = inject('apiClient')
const datasets = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    datasets.value = await apiClient.listDatasets()
  } finally {
    loading.value = false
  }
})

async function deleteDataset(id, name) {
  if (!window.confirm(`Delete "${name}"? This cannot be undone.`)) {
    return
  }
  await apiClient.deleteDataset(id)
  datasets.value = datasets.value.filter(d => d.id !== id)
}
</script>

<template>
  <section class="manager-view">
    <header class="manager-header">
      <h2>Dataset Manager</h2>
    </header>
    <div v-if="loading" class="loading" data-testid="loading">Loading...</div>
    <div v-else-if="datasets.length === 0" class="empty-state" data-testid="empty-state">
      No datasets uploaded yet
      <RouterLink to="/datasets">Upload datasets</RouterLink>
    </div>
    <table v-else class="datasets-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>File Count</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="ds in datasets" :key="ds.id" data-testid="dataset-row">
          <td data-testid="dataset-name">{{ ds.name }}</td>
           <td>{{ ds.file_count ?? '-' }}</td>
          <td data-testid="dataset-status">
            <span class="badge" :class="ds.status">{{ ds.status }}</span>
          </td>
          <td>
            <button class="delete-btn" data-testid="delete-btn" @click="deleteDataset(ds.id, ds.name)">Delete</button>
          </td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<style scoped>
.manager-view { max-width: 900px; }
.manager-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.manager-header h2 { margin: 0; }
.datasets-table { width: 100%; border-collapse: collapse; }
.datasets-table th, .datasets-table td { text-align: left; padding: 0.75rem 1rem; border-bottom: 1px solid var(--border); }
.datasets-table th { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); }
.datasets-table td { font-size: 0.875rem; }
.datasets-table tr:hover td { background: var(--bg-tertiary); }
.badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; }
.badge.idle { background: var(--warning); color: #000; }
.badge.ready { background: var(--success); color: #000; }
.badge.empty { background: var(--bg-tertiary); color: var(--text-secondary); }
.badge.preprocessed { background: var(--accent); color: #000; }
.delete-btn { padding: 0.25rem 0.75rem; background: transparent; border: 1px solid var(--error); color: var(--error); border-radius: 4px; font-size: 0.75rem; cursor: pointer; }
.delete-btn:hover { background: var(--error); color: #000; }
.empty-state { text-align: center; padding: 3rem; color: var(--text-secondary); }
.empty-state a { color: var(--accent); }
.loading { color: var(--text-secondary); padding: 2rem; text-align: center; }
</style>
