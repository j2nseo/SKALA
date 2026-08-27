<script setup>
import { computed, onMounted, ref, watch, watchEffect } from 'vue'
import { useRouter } from 'vue-router'

import BaseDashboardCard from '../components/exercise/BaseDashboardCard.vue'
import ForecastPanel from '../components/exercise/ForecastPanel.vue'
import SearchBar from '../components/exercise/SearchBar.vue'
import WeatherCard from '../components/exercise/WeatherCard.vue'
import { getCurrentWeather, getFiveDayForecast } from '../services/weatherApi'
import { useConfigStore } from '../stores/configStore'

const configStore = useConfigStore()
const router = useRouter()

// 도시 검색과 카드 선택에 필요한 화면 상태
const searchQuery = ref('')
const selectedCity = ref(null)
const statusMessage = ref('카드를 클릭하거나 검색해 보세요.')

const isLoading = ref(false)
const isSearchingCity = ref(false)
const weeklyForecast = ref([])
const searchedWeather = ref(null)

// API 호출에 실패해도 기본 화면을 구성할 수 있는 초기 도시 데이터
const weatherList = ref([
  {
    id: 1,
    city: '서울',
    condition: '맑음',
    temperature: 28,
    icon: '🔥',
    badge: '더움',
    badgeClass: 'hot',
  },
  {
    id: 2,
    city: '수원',
    condition: '비',
    temperature: 24,
    icon: '❄️',
    badge: '선선함',
    badgeClass: 'cool',
  },
  {
    id: 3,
    city: '부산',
    condition: '구름',
    temperature: 26,
    icon: '🔥',
    badge: '더움',
    badgeClass: 'hot',
  },
  {
    id: 4,
    city: '제주',
    condition: '바람',
    temperature: 25,
    icon: '🔥',
    badge: '더움',
    badgeClass: 'hot',
  },
])

// 입력 중에는 도시명을 즉시 필터링하고, API로 검색한 도시는 목록 맨 앞에 배치한다.
const filteredWeatherList = computed(() => {
  const keyword = searchQuery.value.trim().toLocaleLowerCase()
  const allWeather = searchedWeather.value
    ? [searchedWeather.value, ...weatherList.value]
    : weatherList.value

  if (!keyword) {
    return allWeather
  }

  return allWeather.filter((weather) => weather.city.toLocaleLowerCase().includes(keyword))
})

const heroTemperature = computed(() => {
  const temperature = weatherList.value[0]?.temperature

  if (temperature === undefined) {
    return '--'
  }

  return configStore.unit === 'fahrenheit' ? Math.round((temperature * 9) / 5 + 32) : temperature
})

watch(selectedCity, (city) => {
  if (city) {
    console.log('선택 도시 변경:', city.city)
  }
})

watchEffect(() => {
  console.log('검색어 변경:', searchQuery.value)
})

// 검색어 변경과 함께 사용자 안내 문구도 갱신한다.
const handleUpdateQuery = (newQuery) => {
  searchQuery.value = newQuery

  if (newQuery.trim()) {
    statusMessage.value = `"${newQuery}"을 입력했어요. 검색 버튼을 눌러 실제 날씨를 확인하세요.`
  } else {
    statusMessage.value = '카드를 클릭하거나 검색해 보세요.'
  }
}

// 검색 버튼이나 Enter 입력 시 외부 API에서 도시 날씨를 조회한다.
const handleSearchCity = async () => {
  const cityName = searchQuery.value.trim()

  if (!cityName) {
    statusMessage.value = '검색할 도시 이름을 입력해 주세요.'
    return
  }

  isSearchingCity.value = true

  try {
    const weather = await getCurrentWeather(cityName)
    const cityWeather = {
      ...weather,
      ...getBadge(weather.temperature),
    }

    const existingIndex = weatherList.value.findIndex((item) => item.city === weather.city)

    if (existingIndex >= 0) {
      weatherList.value.splice(existingIndex, 1, cityWeather)
      searchedWeather.value = null
    } else {
      searchedWeather.value = cityWeather
    }

    selectedCity.value = cityWeather
    searchQuery.value = ''
    statusMessage.value = `${weather.city}의 실제 날씨를 확인하고 있어요. 다음 검색을 하면 이 결과는 교체됩니다.`
    configStore.markUpdated()
  } catch {
    statusMessage.value = '도시를 찾지 못했어요. 영문 도시 이름으로 다시 검색해 보세요.'
  } finally {
    isSearchingCity.value = false
  }
}

// 카드 선택 상태를 토글해 요약 카드 안에서 상세 정보를 확인한다.
const handleToggleDetail = (weather) => {
  if (selectedCity.value?.id === weather.id) {
    selectedCity.value = null
    statusMessage.value = '상세 날씨를 접었습니다.'
    return
  }

  selectedCity.value = weather
  statusMessage.value = `${weather.city}의 상세 날씨를 확인하고 있어요.`
}

// 상세보기 버튼은 도시 ID를 동적 경로로 전달하고, 검색 도시는 이름도 쿼리에 보존한다.
const handleViewDetail = (weather) => {
  router.push({
    name: 'weather-detail',
    params: { cityId: weather.id },
    query: weather.city ? { city: weather.city } : undefined,
  })
}

const getBadge = (temperature) => {
  if (temperature >= 25) {
    return { icon: '🔥', badge: '더움', badgeClass: 'hot' }
  }

  return { icon: '❄️', badge: '선선함', badgeClass: 'cool' }
}

const loadActualWeather = async () => {
  isLoading.value = true

  try {
    const currentWeatherList = weatherList.value
    const cityNames = currentWeatherList.map((weather) => weather.city)
    const [liveWeatherList, forecast] = await Promise.all([
      Promise.all(cityNames.map((city) => getCurrentWeather(city))),
      getFiveDayForecast('서울'),
    ])

    weatherList.value = liveWeatherList.map((weather, index) => ({
      ...weather,
      id: currentWeatherList[index].id,
      ...getBadge(weather.temperature),
    }))

    weeklyForecast.value = forecast
    configStore.markUpdated()
  } catch (error) {
    statusMessage.value = error.message
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadActualWeather()
})
</script>

<template>
  <main class="weather-page">
    <div class="weather-container">
      <header class="dashboard-heading">
        <div>
          <p>MONITORING CENTER</p>
          <h1>날씨 대시보드</h1>
        </div>

        <el-button
          class="refresh-button"
          :loading="isLoading"
          round
          type="primary"
          aria-label="날씨 업데이트"
          title="날씨 업데이트"
          @click="loadActualWeather"
        >
          ↻
        </el-button>
      </header>

      <section class="hero">
        <div class="hero-copy">
          <span class="hero-chip">● LIVE WEATHER</span>
          <h2>오늘의 날씨,<br />한 화면에서 관리하세요.</h2>
          <p>도시별 현재 날씨와 생활 정보를 빠르게 확인할 수 있어요.</p>
        </div>

        <div class="hero-weather">
          <span>{{ weatherList[0]?.condition || '날씨' }}</span>
          <strong
            >{{ heroTemperature }}<small>{{ configStore.unitSymbol }}</small></strong
          >
          <p>{{ weatherList[0]?.city || '서울' }} 기준 · {{ configStore.formattedLastUpdated }}</p>
        </div>
      </section>

      <div class="dashboard-grid">
        <BaseDashboardCard icon="🔍" title="도시 검색">
          <SearchBar
            :query="searchQuery"
            @update-query="handleUpdateQuery"
            @search-city="handleSearchCity"
          />

          <p v-if="isSearchingCity" class="search-loading">도시의 실제 날씨를 찾는 중이에요.</p>

          <div class="quick-guide">
            <span>QUICK TIP</span>
            <p>도시 카드를 선택하면 상세 날씨를 확인할 수 있어요.</p>
          </div>
        </BaseDashboardCard>

        <BaseDashboardCard class="weather-overview-card" icon="🏙️" title="지역별 날씨 현황">
          <div v-if="filteredWeatherList.length > 0" class="weather-list">
            <WeatherCard
              v-for="weather in filteredWeatherList"
              :key="weather.id"
              :weather="weather"
              :selected="selectedCity?.id === weather.id"
              @toggle-detail="handleToggleDetail"
              @view-detail="handleViewDetail"
            />
          </div>

          <p v-else class="empty-message">검색 결과가 없습니다.</p>
        </BaseDashboardCard>
      </div>

      <BaseDashboardCard v-if="weeklyForecast.length" icon="📈" title="서울 5일 예보">
        <ForecastPanel :forecast="weeklyForecast" />
      </BaseDashboardCard>

      <div class="status-panel">
        {{ statusMessage }}
      </div>
    </div>
  </main>
</template>

<style scoped>
.weather-page {
  min-height: 100vh;
  padding: 42px 34px 72px;
  background: #f7f6ff;
}

.weather-container {
  width: min(100%, 1440px);
  margin: 0 auto;
}

.dashboard-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 26px;
}

.dashboard-heading p {
  margin: 0 0 10px;
  color: #7c3aed;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 1.4px;
}

.dashboard-heading h1 {
  margin: 0;
  color: #25233a;
  font-size: 29px;
  letter-spacing: -1px;
}

.refresh-button {
  --el-button-bg-color: #7c3aed;
  --el-button-border-color: #7c3aed;
  --el-button-hover-bg-color: #6d28d9;
  --el-button-hover-border-color: #6d28d9;
  --el-button-active-bg-color: #5b21b6;
  --el-button-active-border-color: #5b21b6;
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 20px;
  padding: 34px 38px;
  overflow: hidden;
  color: white;
  background:
    radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.28), transparent 12%),
    linear-gradient(130deg, #6d28d9, #7c3aed 50%, #a855f7);
  border-radius: 20px;
  box-shadow: 0 16px 30px rgba(109, 40, 217, 0.22);
}

.hero-chip {
  display: inline-block;
  padding: 7px 10px;
  color: #f5f3ff;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 1px;
  background: rgba(255, 255, 255, 0.16);
  border-radius: 999px;
}

.hero h2 {
  margin: 18px 0 10px;
  font-size: clamp(26px, 4vw, 40px);
  line-height: 1.2;
  letter-spacing: -1.5px;
}

.hero-copy > p {
  margin: 0;
  color: #ede9fe;
}

.hero-weather {
  display: flex;
  align-items: flex-end;
  flex-direction: column;
  justify-content: center;
  min-width: 160px;
}

.hero-weather > span {
  color: #e9d5ff;
  font-size: 15px;
  font-weight: 700;
}

.hero-weather strong {
  margin-top: 2px;
  font-size: 62px;
  line-height: 1;
  letter-spacing: -3px;
}

.hero-weather small {
  margin-left: 4px;
  font-size: 23px;
  letter-spacing: 0;
}

.hero-weather p {
  margin: 8px 0 0;
  color: #ede9fe;
  font-size: 13px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(270px, 0.72fr) minmax(500px, 1.65fr);
  gap: 20px;
  align-items: start;
}

.dashboard-grid :deep(.dashboard-card) {
  margin-bottom: 0;
}

.dashboard-grid :deep(.weather-overview-card) {
  background: rgba(255, 255, 255, 0.5);
  border-color: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(18px);
}

.quick-guide {
  margin-top: 22px;
  padding: 18px;
  color: #5b21b6;
  background: linear-gradient(135deg, #f3e8ff, #faf5ff);
  border: 1px solid #e9d5ff;
  border-radius: 12px;
}

.quick-guide span {
  color: #8b5cf6;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 1.1px;
}

.quick-guide p {
  margin: 8px 0 0;
  font-size: 14px;
  line-height: 1.6;
}

.search-loading {
  margin: 12px 0 0;
  color: #7c3aed;
  font-size: 14px;
}

.weather-list {
  padding: 4px;
}

.empty-message {
  padding: 30px;
  color: #64748b;
  text-align: center;
  background-color: #f8fafc;
  border-radius: 8px;
}

.status-panel {
  padding: 18px 22px;
  color: #6d28d9;
  font-weight: bold;
  text-align: center;
  background: #f5f3ff;
  border: 1px solid #ddd6fe;
  border-radius: 12px;
  box-shadow: 0 8px 18px rgba(109, 40, 217, 0.05);
}

@media (max-width: 600px) {
  .weather-page {
    padding: 28px 18px 48px;
  }

  .hero {
    align-items: flex-start;
    flex-direction: column;
    padding: 28px;
  }

  .hero-weather {
    align-items: flex-start;
  }
}

@media (max-width: 980px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}
</style>
