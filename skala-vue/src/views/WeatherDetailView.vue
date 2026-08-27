<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useConfigStore } from '../stores/configStore'
import { getCurrentWeather } from '../services/weatherApi'

// 동적 경로의 도시 ID와 화면 이동을 위한 Router 인스턴스
const route = useRoute()
const router = useRouter()

const configStore = useConfigStore()

// 상세 화면의 조회 결과와 존재 여부
const selectedWeather = ref(null)
const cityNotFound = ref(false)

// API 요청이 불가능할 때 도시 ID로 조회할 기본 데이터
const weatherList = [
  {
    id: 1,
    city: '서울',
    condition: '맑음',
    temperature: 28,
    humidity: 55,
    windSpeed: 2.3,
    description: '햇빛이 강하고 대체로 맑은 날씨입니다.',
  },
  {
    id: 2,
    city: '수원',
    condition: '비',
    temperature: 24,
    humidity: 82,
    windSpeed: 3.1,
    description: '비가 내리고 있으니 우산을 준비하세요.',
  },
  {
    id: 3,
    city: '부산',
    condition: '구름',
    temperature: 26,
    humidity: 70,
    windSpeed: 4.2,
    description: '구름이 많고 해안가에는 바람이 불고 있습니다.',
  },
  {
    id: 4,
    city: '제주',
    condition: '바람',
    temperature: 25,
    humidity: 68,
    windSpeed: 6.2,
    description: '바람이 강할 수 있으니 해안가 활동에 유의하세요.',
  },
]

// 검색 도시라면 API를 우선 사용하고, 기본 도시는 ID로 대체 데이터를 찾는다.
onMounted(async () => {
  const cityName = route.query.city
  const cityId = Number(route.params.cityId)

  if (cityName) {
    try {
      const liveWeather = await getCurrentWeather(cityName)
      selectedWeather.value = {
        ...liveWeather,
        description: liveWeather.description || '현재 날씨 정보를 확인해 보세요.',
      }
      return
    } catch {
      // 네트워크 오류 시 같은 ID의 기본 데이터로 이어서 조회한다.
    }
  }

  selectedWeather.value = weatherList.find((weather) => weather.id === cityId)
  cityNotFound.value = !selectedWeather.value
})

const goBack = () => {
  router.back()
}

const goHome = () => {
  router.push('/')
}

const displayTemp = computed(() => {
  if (!selectedWeather.value) {
    return ''
  }

  const rawTemp = selectedWeather.value.temperature

  if (configStore.unit === 'fahrenheit') {
    return Math.round((rawTemp * 9) / 5 + 32)
  }

  return rawTemp
})
</script>

<template>
  <main class="detail-page">
    <section v-if="selectedWeather" class="detail-card">
      <h1>🌤️ {{ selectedWeather.city }} 상세 날씨</h1>

      <div class="weather-information">
        <p>
          <strong>현재 날씨</strong>
          <span>{{ selectedWeather.condition }}</span>
        </p>

        <p>
          <strong>현재 기온</strong>
          <span>{{ displayTemp }}{{ configStore.unitSymbol }}</span>
        </p>

        <p>
          <strong>습도</strong>
          <span>{{ selectedWeather.humidity }}%</span>
        </p>

        <p>
          <strong>풍속</strong>
          <span>{{ selectedWeather.windSpeed }}m/s</span>
        </p>
      </div>

      <div class="description">
        {{ selectedWeather.description }}
      </div>

      <div class="button-group">
        <button @click="goBack">이전 페이지</button>

        <button @click="goHome">메인으로</button>
      </div>
    </section>

    <section v-else-if="cityNotFound" class="not-found-card">
      <h1>도시 정보를 찾을 수 없습니다.</h1>

      <p>
        요청한 도시 ID:
        <strong>{{ route.params.cityId }}</strong>
      </p>

      <button @click="goHome">날씨 대시보드로 돌아가기</button>
    </section>

    <p v-else class="loading-message">날씨 정보를 불러오는 중입니다.</p>
  </main>
</template>

<style scoped>
.detail-page {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-height: 100vh;
  padding: 42px 34px 72px;
  background: #f7f6ff;
}

.detail-card,
.not-found-card {
  width: 100%;
  max-width: 1280px;
  padding: 42px;
  background-color: white;
  border: 1px solid #eceaf5;
  border-radius: 20px;
  box-shadow: 0 14px 34px rgba(58, 44, 116, 0.08);
}

.detail-card h1,
.not-found-card h1 {
  margin: 0 0 28px;
  color: #1e293b;
  font-family: Outfit, 'Noto Sans KR', sans-serif;
  font-size: clamp(28px, 3vw, 42px);
  letter-spacing: -1.5px;
}

.weather-information {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.weather-information p {
  display: flex;
  justify-content: space-between;
  margin: 0;
  padding: 16px;
  background-color: #f8fafc;
  border-radius: 8px;
}

.weather-information strong {
  color: #334155;
}

.weather-information span {
  color: #2563eb;
  font-weight: bold;
}

.description {
  margin-top: 20px;
  padding: 18px;
  color: #166534;
  line-height: 1.7;
  background-color: #dcfce7;
  border-radius: 8px;
}

@media (max-width: 700px) {
  .detail-page {
    padding: 28px 18px 48px;
  }

  .detail-card,
  .not-found-card {
    padding: 26px;
  }

  .weather-information {
    grid-template-columns: 1fr;
  }
}

.button-group {
  display: flex;
  gap: 10px;
  margin-top: 24px;
}

button {
  padding: 10px 16px;
  color: white;
  background-color: #2563eb;
  border: none;
  border-radius: 7px;
  cursor: pointer;
}

button:hover {
  background-color: #1d4ed8;
}

.not-found-card {
  text-align: center;
}

.not-found-card p {
  color: #64748b;
}

.loading-message {
  color: #475569;
  font-weight: bold;
}
</style>
