import './style.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router/index.js'
import { MockApiClient } from './mocks/mockApiClient.js'

const app = createApp(App)

// Mock-data seam: inject the API-client abstraction. Swap the implementation
// here (e.g. a REST client) when the real backend API lands (M4).
app.provide('apiClient', new MockApiClient())

app.use(createPinia())
app.use(router)
app.mount('#app')
