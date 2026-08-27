<script setup>
import { ref } from 'vue'

const guides = ref([
  {
    id: 1,
    icon: '☀️',
    condition: '맑은 날',
    description: '자외선 지수를 확인하고 야외 활동을 준비하세요.',
    recommendations: ['선크림 사용', '선글라스 착용', '충분한 수분 섭취'],
  },
  {
    id: 2,
    icon: '🌧️',
    condition: '비 오는 날',
    description: '강수량과 도로 상황을 확인한 후 이동하세요.',
    recommendations: ['우산 준비', '미끄럼 방지 신발', '대중교통 지연 확인'],
  },
  {
    id: 3,
    icon: '🌬️',
    condition: '바람이 강한 날',
    description: '강풍으로 인한 낙하물과 시설물에 주의하세요.',
    recommendations: ['야외 물건 고정', '해안가 접근 주의', '외출 전 풍속 확인'],
  },
  {
    id: 4,
    icon: '❄️',
    condition: '추운 날',
    description: '체온을 유지하고 빙판길 사고에 대비하세요.',
    recommendations: ['여러 겹으로 착용', '장갑과 목도리 준비', '빙판길 주의'],
  },
])
</script>

<template>
  <main class="guide-page">
    <section class="guide-container">
      <header>
        <p class="category">WEATHER GUIDE</p>
        <h1>🌿 날씨별 생활 가이드</h1>

        <p class="introduction">
          날씨 상황에 맞는 준비 사항을 확인하고 안전한 하루를 계획해 보세요.
        </p>
      </header>

      <div class="guide-grid">
        <article v-for="guide in guides" :key="guide.id" class="guide-card">
          <span class="weather-icon">{{ guide.icon }}</span>

          <h2>{{ guide.condition }}</h2>

          <p>{{ guide.description }}</p>

          <ul>
            <li v-for="recommendation in guide.recommendations" :key="recommendation">
              {{ recommendation }}
            </li>
          </ul>
        </article>
      </div>

      <RouterLink class="home-link" to="/"> 날씨 대시보드로 돌아가기 </RouterLink>
    </section>
  </main>
</template>

<style scoped>
.guide-page {
  min-height: 100vh;
  padding: 50px 20px;
  background-color: #f0fdf4;
}

.guide-container {
  max-width: 960px;
  margin: 0 auto;
}

header {
  margin-bottom: 30px;
  text-align: center;
}

.category {
  margin: 0 0 8px;
  color: #16a34a;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 2px;
}

h1 {
  margin: 0;
  color: #14532d;
  font-size: 32px;
}

.introduction {
  margin: 14px 0 0;
  color: #4b5563;
  line-height: 1.7;
}

.guide-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 18px;
}

.guide-card {
  padding: 26px;
  background-color: white;
  border: 1px solid #bbf7d0;
  border-radius: 14px;
  box-shadow: 0 6px 18px rgba(20, 83, 45, 0.08);
}

.weather-icon {
  font-size: 34px;
}

.guide-card h2 {
  margin: 12px 0 10px;
  color: #166534;
  font-size: 20px;
}

.guide-card p {
  color: #64748b;
  line-height: 1.6;
}

.guide-card ul {
  margin: 16px 0 0;
  padding-left: 20px;
  color: #334155;
  line-height: 1.9;
}

.home-link {
  display: block;
  width: fit-content;
  margin: 30px auto 0;
  padding: 11px 18px;
  color: white;
  font-weight: 700;
  text-decoration: none;
  background-color: #16a34a;
  border-radius: 7px;
}

.home-link:hover {
  background-color: #15803d;
}

@media (max-width: 650px) {
  .guide-grid {
    grid-template-columns: 1fr;
  }
}
</style>
