import { defineStore } from 'pinia'

export const useConfigStore = defineStore('config', {
  state: () => ({
    unit: 'celsius',
    lastUpdated: null,
  }),

  getters: {
    unitSymbol: (state) => (state.unit === 'celsius' ? '℃' : '℉'),
    formattedLastUpdated: (state) => {
      if (!state.lastUpdated) {
        return '업데이트 전'
      }

      return new Intl.DateTimeFormat('ko-KR', {
        hour: '2-digit',
        minute: '2-digit',
      }).format(state.lastUpdated)
    },
  },

  actions: {
    toggleUnit() {
      this.unit = this.unit === 'celsius' ? 'fahrenheit' : 'celsius'
    },

    markUpdated() {
      this.lastUpdated = new Date()
    },
  },
})
