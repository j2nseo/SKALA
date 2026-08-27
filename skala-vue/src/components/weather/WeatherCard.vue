<script setup>
// 부모로부터 날씨 객체와 선택 여부를 받습니다.
defineProps({
  weather: {
    type: Object,
    required: true,
  },

  selected: {
    type: Boolean,
    default: false,
  },
})

// 부모에게 보낼 이벤트를 등록합니다.
const emit = defineEmits(['select-card', 'click-detail'])
</script>

<template>
  <article
    class="weather-card"
    :class="{ selected: selected }"
    @click="emit('select-card', weather)"
  >
    <div class="weather-information">
      <h3>{{ weather.city }} ({{ weather.condition }})</h3>

      <p>현재 기온: {{ weather.temperature }}℃</p>

      <span class="weather-badge" :class="weather.badgeClass">
        {{ weather.icon }} {{ weather.badge }}
      </span>
    </div>

    <button type="button" @click.stop="emit('click-detail', weather)">상세보기</button>
  </article>
</template>

<style scoped>
.weather-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 18px;
  background-color: white;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  transition: 0.2s;
}

.weather-card:hover {
  border-color: #60a5fa;
  transform: translateY(-2px);
}

.weather-card.selected {
  background-color: #eff6ff;
  border-color: #2563eb;
}

.weather-information h3 {
  margin: 0 0 8px;
  color: #334155;
  font-size: 17px;
}

.weather-information p {
  margin: 0 0 10px;
  color: #64748b;
}

.weather-badge {
  display: inline-block;
  padding: 5px 9px;
  color: white;
  font-size: 13px;
  border-radius: 5px;
}

.hot {
  background-color: #fb7185;
}

.cool {
  background-color: #38bdf8;
}

.normal {
  background-color: #22c55e;
}

button {
  padding: 9px 12px;
  color: #334155;
  background-color: white;
  border: 1px solid #94a3b8;
  border-radius: 5px;
  cursor: pointer;
}

button:hover {
  background-color: #f1f5f9;
}
</style>
