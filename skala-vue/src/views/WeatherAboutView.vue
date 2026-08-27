<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}
</script>

<template>
  <main class="about-page">
    <section class="about-card">
      <h1>🌤️ 날씨 대시보드 소개</h1>

      <p class="introduction">
        도시별 현재 날씨를 검색하고 상세 기상 정보를 확인할 수 있는 Vue 기반 날씨 대시보드입니다.
      </p>

      <div class="feature-list">
        <article>
          <h2>🔍 도시 검색</h2>
          <p>도시 이름을 입력하면 검색 결과가 실시간으로 반영됩니다.</p>
        </article>

        <article>
          <h2>🏙️ 지역별 날씨</h2>
          <p>서울, 수원, 부산의 날씨와 현재 기온을 확인할 수 있습니다.</p>
        </article>

        <article>
          <h2>📋 상세 기상 정보</h2>
          <p>도시별 기온, 습도, 풍속과 날씨 설명을 제공합니다.</p>
        </article>

        <article>
          <h2>🧭 페이지 이동</h2>
          <p>Vue Router를 사용해 새로고침 없이 화면을 전환합니다.</p>
        </article>
      </div>

      <button @click="goHome">날씨 대시보드로 돌아가기</button>
    </section>
  </main>
</template>

<style scoped>
.about-page {
  min-height: 100vh;
  padding: 60px 20px;
  background-color: #eaf4fb;
}

.about-card {
  max-width: 760px;
  margin: 0 auto;
  padding: 36px;
  background-color: white;
  border: 1px solid #cbd5e1;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.1);
}

.about-card > h1 {
  margin: 0 0 18px;
  color: #1e293b;
  font-size: 30px;
}

.introduction {
  margin-bottom: 30px;
  color: #475569;
  line-height: 1.8;
}

.feature-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.feature-list article {
  padding: 20px;
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
}

.feature-list h2 {
  margin: 0 0 10px;
  color: #334155;
  font-size: 18px;
}

.feature-list p {
  margin: 0;
  color: #64748b;
  line-height: 1.6;
}

button {
  margin-top: 28px;
  padding: 11px 18px;
  color: white;
  background-color: #2563eb;
  border: none;
  border-radius: 7px;
  cursor: pointer;
}

button:hover {
  background-color: #1d4ed8;
}

@media (max-width: 600px) {
  .feature-list {
    grid-template-columns: 1fr;
  }
}
</style>
