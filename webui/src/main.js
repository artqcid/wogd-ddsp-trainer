import './style.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router/index.js'
import { RestApiClient } from './api/restApiClient.js'

const app = createApp(App)

app.provide('apiClient', new RestApiClient())

app.use(createPinia())
app.use(router)
app.mount('#app')
