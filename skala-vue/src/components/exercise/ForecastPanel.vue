<script setup>
import { computed } from 'vue'

import { useConfigStore } from '../../stores/configStore'

const props = defineProps({
  forecast: {
    type: Array,
    default: () => [],
  },
})

const configStore = useConfigStore()

const displayForecast = computed(() => {
  return props.forecast.map((item) => ({
    ...item,
    displayTemp:
      configStore.unit === 'fahrenheit'
        ? Math.round((item.temperature * 9) / 5 + 32)
        : item.temperature,
  }))
})

const icons = {
  맑음: '☀️',
  구름: '☁️',
  비: '🌧️',
  이슬비: '🌦️',
  눈: '❄️',
  안개: '🌫️',
}
</script>

<template>
  <div class="forecast-list">
    <article v-for="item in displayForecast" :key="item.date" class="forecast-item">
      <span>{{ item.date }}</span>
      <strong>{{ icons[item.condition] || '🌤️' }}</strong>
      <p>{{ item.condition }}</p>
      <b>{{ item.displayTemp }}{{ configStore.unitSymbol }}</b>
    </article>
  </div>
</template>

<style scoped>
.forecast-list {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.forecast-item {
  padding: 18px 12px;
  text-align: center;
  background: #faf9ff;
  border: 1px solid #eeeafb;
  border-radius: 12px;
}

.forecast-item > span,
.forecast-item p {
  color: #6b7280;
  font-size: 13px;
}

.forecast-item strong {
  display: block;
  margin: 11px 0 7px;
  font-size: 27px;
}

.forecast-item p {
  margin: 0 0 8px;
}

.forecast-item b {
  color: #6d28d9;
  font-size: 16px;
}

@media (max-width: 680px) {
  .forecast-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
