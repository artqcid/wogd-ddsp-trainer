import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: () => import('../views/HealthView.vue'),
  },
  {
    path: '/datasets',
    name: 'datasets',
    component: () => import('../views/UploadIngestionView.vue'),
  },
  {
    path: '/datasets/manager',
    name: 'dataset-manager',
    component: () => import('../views/DatasetManagerView.vue'),
  },
  {
    path: '/datasets/preprocess',
    name: 'preprocessing',
    component: () => import('../views/PreprocessingView.vue'),
  },
  {
    path: '/model',
    name: 'model-config',
    component: () => import('../views/TrainingConfigView.vue'),
  },
  {
    path: '/training',
    name: 'training',
    component: () => import('../views/TrainingDashboardView.vue'),
  },
  {
    path: '/inference',
    name: 'inference',
    component: () => import('../views/InferencePlaygroundView.vue'),
  },
  {
    path: '/export',
    name: 'export',
    component: () => import('../views/ModelExportView.vue'),
  },
  {
    path: '/presets',
    name: 'presets',
    component: () => import('../views/PresetManagerView.vue'),
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('../views/SettingsView.vue'),
  },
  {
    path: '/experimental/reverb',
    name: 'reverb-ir',
    component: () => import('../views/ReverbInjectionView.vue'),
  },
  {
    path: '/experimental/f0-editor',
    name: 'f0-editor',
    component: () => import('../views/F0EditorView.vue'),
  },
  {
    path: '/experimental/mixer',
    name: 'component-mixer',
    component: () => import('../views/ComponentMixerView.vue'),
  },
  {
    path: '/experimental/synth-hacks',
    name: 'synth-hacks',
    component: () => import('../views/SynthHacksView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
