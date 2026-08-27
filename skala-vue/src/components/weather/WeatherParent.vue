<script setup>
import { computed, ref } from 'vue'

import BaseDashboardCard from './BaseDashboardCard.vue'
import SearchBar from './SearchBar.vue'
import WeatherCard from './WeatherCard.vue'

// 검색창에 입력된 검색어
const searchQuery = ref('')

// 현재 선택한 도시
const selectedCity = ref(null)

// 화면 아래에 표시되는 안내 문구
const statusMessage = ref('카드를 클릭하거나 검색해 보세요.')

// 전체 도시 날씨 데이터
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
])

// 검색어에 맞는 도시만 골라냅니다.
const filteredWeatherList = computed(() => {
  const keyword = searchQuery.value.trim()

  if (!keyword) {
    return weatherList.value
  }

  return weatherList.value.filter((weather) => {
    return weather.city.includes(keyword)
  })
})

// SearchBar가 보낸 검색어를 받습니다.
const handleUpdateQuery = (newQuery) => {
  searchQuery.value = newQuery

  if (newQuery.trim()) {
    statusMessage.value = `"${newQuery}" 검색 결과입니다.`
  } else {
    statusMessage.value = '카드를 클릭하거나 검색해 보세요.'
  }
}

// WeatherCard가 보낸 카드 선택 이벤트를 처리합니다.
const handleSelectCard = (weather) => {
  selectedCity.value = weather
  statusMessage.value = `${weather.city} 카드를 선택했습니다.`
}

// WeatherCard가 보낸 상세보기 이벤트를 처리합니다.
const handleClickDetail = (weather) => {
  selectedCity.value = weather

  statusMessage.value =
    `${weather.city}의 현재 날씨는 ${weather.condition}, ` + `기온은 ${weather.temperature}℃입니다.`

  alert(
    `${weather.city} 날씨 상세 정보\n` +
      `날씨: ${weather.condition}\n` +
      `현재 기온: ${weather.temperature}℃`,
  )
}
</script>

<template>
  <main class="weather-page">
    <div class="weather-container">
      <h1>🌤️ 과제 3: 날씨 (컴포넌트)</h1>

      <!-- 도시 검색 영역 -->
      <BaseDashboardCard icon="🔍" title="도시 검색 (한글 즉시 동기화)">
        <SearchBar :query="searchQuery" @update-query="handleUpdateQuery" />
      </BaseDashboardCard>

      <!-- 지역별 날씨 목록 -->
      <BaseDashboardCard icon="🏙️" title="지역별 날씨 현황">
        <div v-if="filteredWeatherList.length > 0" class="weather-list">
          <WeatherCard
            v-for="weather in filteredWeatherList"
            :key="weather.id"
            :weather="weather"
            :selected="selectedCity?.id === weather.id"
            @select-card="handleSelectCard"
            @click-detail="handleClickDetail"
          />
        </div>

        <p v-else class="empty-message">검색 결과가 없습니다.</p>
      </BaseDashboardCard>

      <!-- 현재 상태 안내 -->
      <div class="status-panel">
        {{ statusMessage }}
      </div>
    </div>
  </main>
</template>

<style scoped>
.weather-page {
  min-height: 100vh;
  padding: 40px 20px;
  background-color: #eaf4fb;
}

.weather-container {
  max-width: 760px;
  margin: 0 auto;
}

.weather-container > h1 {
  margin: 0 0 24px;
  color: #1e293b;
  font-size: 28px;
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
  padding: 18px;
  color: #15803d;
  font-weight: bold;
  text-align: center;
  background-color: #dcfce7;
  border: 1px solid #86efac;
  border-radius: 8px;
}
</style>
