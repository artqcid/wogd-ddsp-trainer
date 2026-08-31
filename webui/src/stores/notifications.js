import { defineStore } from 'pinia'

let nextId = 0

export const useNotificationsStore = defineStore('notifications', {
  state: () => ({
    items: [],
  }),
  actions: {
    notify(kind, message, { timeout = 5000 } = {}) {
      const id = nextId++
      this.items.push({ id, kind, message })
      if (timeout > 0) {
        setTimeout(() => this.dismiss(id), timeout)
      }
      return id
    },
    info(message, opts) { return this.notify('info', message, opts) },
    success(message, opts) { return this.notify('success', message, opts) },
    warn(message, opts) { return this.notify('warn', message, opts) },
    error(message, opts) { return this.notify('error', message, opts) },
    dismiss(id) {
      this.items = this.items.filter(i => i.id !== id)
    },
  },
})