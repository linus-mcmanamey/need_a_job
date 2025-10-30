import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export const useSearchConfigStore = defineStore('searchConfig', {
  state: () => ({
    config: null,
    loading: false,
    error: null
  }),

  actions: {
    async loadConfig() {
      this.loading = true
      this.error = null

      try {
        const response = await axios.get(`${API_BASE_URL}/config/search`)
        this.config = response.data
        console.log('[SearchConfig] Configuration loaded:', this.config)
        return this.config
      } catch (error) {
        console.error('[SearchConfig] Error loading config:', error)
        this.error = error.response?.data?.message || error.message || 'Failed to load configuration'
        throw error
      } finally {
        this.loading = false
      }
    },

    async saveConfig(configData) {
      this.loading = true
      this.error = null

      try {
        const response = await axios.put(`${API_BASE_URL}/config/search`, configData)
        this.config = response.data
        console.log('[SearchConfig] Configuration saved successfully')
        return this.config
      } catch (error) {
        console.error('[SearchConfig] Error saving config:', error)
        this.error = error.response?.data?.message || error.message || 'Failed to save configuration'
        throw error
      } finally {
        this.loading = false
      }
    }
  }
})
