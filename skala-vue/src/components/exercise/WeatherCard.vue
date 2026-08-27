<script setup>
import { computed } from 'vue'

import { useConfigStore } from '../../stores/configStore'

// 카드 렌더링에 필요한 날씨 데이터와 선택 상태
const props = defineProps({
  weather: {
    type: Object,
    required: true,
  },

  selected: {
    type: Boolean,
    default: false,
  },
})

// 카드 선택과 상세 페이지 이동을 각각 분리한 사용자 이벤트
const emit = defineEmits(['toggle-detail', 'view-detail'])

const configStore = useConfigStore()

const displayTemp = computed(() => {
  const rawTemp = props.weather.temperature

  if (configStore.unit === 'fahrenheit') {
    return Math.round((rawTemp * 9) / 5 + 32)
  }

  return rawTemp
})

const displayFeelsLike = computed(() => {
  const rawTemp = props.weather.feelsLike ?? props.weather.temperature

  if (configStore.unit === 'fahrenheit') {
    return Math.round((rawTemp * 9) / 5 + 32)
  }

  return rawTemp
})

const conditionIcon = computed(() => {
  const icons = {
    맑음: '☀️',
    구름: '☁️',
    비: '🌧️',
    이슬비: '🌦️',
    눈: '❄️',
    안개: '🌫️',
  }

  return icons[props.weather.condition] || '🌤️'
})

const weatherAdvice = computed(() => {
  const adviceByCondition = {
    비: '우산을 챙기고, 미끄러운 길을 조심하세요.',
    이슬비: '작은 우산이나 가벼운 겉옷을 준비하세요.',
    눈: '길이 미끄러울 수 있으니 천천히 이동하세요.',
    맑음: '햇볕이 강할 수 있어 자외선 차단을 추천해요.',
    구름: '큰 일교차에 대비해 얇은 겉옷이 좋아요.',
    안개: '시야가 좁아질 수 있으니 이동 시 주의하세요.',
  }

  return adviceByCondition[props.weather.condition] || '현재 날씨를 확인하고 즐거운 하루 보내세요.'
})
</script>

<template>
  <article
    class="weather-card"
    :class="{ selected: selected }"
    role="button"
    tabindex="0"
    @click="emit('toggle-detail', weather)"
    @keydown.enter="emit('toggle-detail', weather)"
  >
    <div class="weather-information">
      <span class="condition-icon">{{ conditionIcon }}</span>

      <div>
        <div class="city-heading">
          <h3>{{ weather.city }}</h3>
          <span class="condition-label">{{ weather.condition }}</span>
        </div>

        <p class="temperature-text">현재 {{ displayTemp }}{{ configStore.unitSymbol }}</p>

        <span class="weather-badge" :class="weather.badgeClass">
          {{ weather.icon }} {{ weather.badge }}
        </span>
      </div>
    </div>

    <button class="detail-button" type="button" @click.stop="emit('view-detail', weather)">
      상세 페이지
    </button>

    <transition name="expand">
      <div v-if="selected" class="detail-information">
        <div class="detail-overview">
          <span class="detail-icon">{{ conditionIcon }}</span>
          <div>
            <span>현재 {{ weather.city }} 날씨</span>
            <strong>{{ displayTemp }}{{ configStore.unitSymbol }}</strong>
            <p>{{ weather.description || `${weather.condition} 상태의 현재 날씨입니다.` }}</p>
          </div>
        </div>

        <div class="weather-stat">
          <span>🌡️ 체감 온도</span>
          <strong>{{ displayFeelsLike }}{{ configStore.unitSymbol }}</strong>
        </div>
        <div class="weather-stat">
          <span>💧 습도</span>
          <strong>{{ weather.humidity ?? '--' }}%</strong>
        </div>
        <div class="weather-stat">
          <span>💨 풍속</span>
          <strong>{{ weather.windSpeed ?? '--' }}m/s</strong>
        </div>
        <div class="weather-stat">
          <span>⏱️ 기압</span>
          <strong>{{ weather.pressure ?? '--' }}hPa</strong>
        </div>

        <p class="weather-advice">💡 {{ weatherAdvice }}</p>
      </div>
    </transition>
  </article>
</template>

<style scoped>
.weather-card {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.66);
  border: 1px solid rgba(255, 255, 255, 0.82);
  border-radius: 14px;
  backdrop-filter: blur(12px);
  cursor: pointer;
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.025);
  transition: 0.2s ease;
}

.weather-card:hover {
  background: rgba(255, 255, 255, 0.88);
  border-color: #c4b5fd;
  box-shadow: 0 12px 24px rgba(124, 58, 237, 0.14);
  transform: translateY(-2px);
}

.weather-card:focus-visible {
  outline: 3px solid rgba(124, 58, 237, 0.35);
  outline-offset: 3px;
}

.weather-card.selected {
  background: rgba(245, 243, 255, 0.82);
  border-color: #8b5cf6;
}

.detail-button {
  padding: 9px 13px;
  color: #6d28d9;
  font-size: 13px;
  font-weight: 800;
  background: white;
  border: 1px solid #c4b5fd;
  border-radius: 9px;
  cursor: pointer;
}

.detail-button:hover {
  color: white;
  background: #7c3aed;
  border-color: #7c3aed;
}

.weather-information h3 {
  margin: 0;
  color: #24223b;
  font-size: 19px;
  font-weight: 800;
  letter-spacing: -0.6px;
}

.city-heading {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 7px;
}

.condition-label {
  padding: 3px 8px;
  color: #6d28d9;
  font-size: 11px;
  font-weight: 800;
  background: #ede9fe;
  border-radius: 999px;
}

.weather-information {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.condition-icon {
  display: grid;
  place-items: center;
  flex: 0 0 48px;
  width: 48px;
  height: 48px;
  font-size: 25px;
  background: #f5f3ff;
  border-radius: 14px;
}

.temperature-text {
  margin: 0 0 10px;
  color: #64748b;
  font-size: 14px;
  font-weight: 600;
}

.detail-information {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  width: 100%;
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid #ddd6fe;
}

.detail-overview {
  display: flex;
  grid-column: 1 / -1;
  gap: 15px;
  align-items: center;
  padding: 16px;
  background: linear-gradient(120deg, #ede9fe, #faf5ff);
  border-radius: 14px;
}

.detail-icon {
  display: grid;
  place-items: center;
  flex: 0 0 58px;
  width: 58px;
  height: 58px;
  font-size: 31px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 18px rgba(91, 33, 182, 0.12);
}

.detail-overview > div > span,
.weather-stat span {
  display: block;
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
}

.detail-overview strong {
  display: block;
  margin-top: 2px;
  color: #4c1d95;
  font-size: 28px;
  letter-spacing: -1px;
}

.detail-overview p {
  margin: 3px 0 0;
  color: #64748b;
  font-size: 13px;
}

.weather-stat {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 12px;
}

.weather-stat strong {
  color: #5b21b6;
  font-size: 18px;
}

.weather-advice {
  grid-column: 1 / -1;
  margin: 2px 0 0;
  padding: 13px 14px;
  color: #475569;
  font-size: 14px;
  line-height: 1.65;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 12px;
}

.expand-enter-active,
.expand-leave-active {
  overflow: hidden;
  transition: all 0.28s ease;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-8px);
}

.expand-enter-to,
.expand-leave-from {
  max-height: 500px;
  opacity: 1;
  transform: translateY(0);
}

@media (max-width: 620px) {
  .detail-information {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
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
</style>
