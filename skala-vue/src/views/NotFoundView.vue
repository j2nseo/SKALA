<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  router.back()
}
</script>

<template>
  <main class="not-found-page">
    <section class="not-found-card">
      <p class="error-code">404</p>

      <h1>페이지를 찾을 수 없습니다.</h1>

      <p class="description">요청한 주소가 잘못되었거나 페이지가 이동되었습니다.</p>

      <div class="button-group">
        <button class="secondary-button" @click="goBack">이전 페이지</button>

        <button @click="goHome">날씨 대시보드</button>
      </div>
    </section>
  </main>
</template>

<style scoped>
.not-found-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
  background-color: #eaf4fb;
}

.not-found-card {
  width: 100%;
  max-width: 560px;
  padding: 48px 32px;
  text-align: center;
  background-color: white;
  border: 1px solid #cbd5e1;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.1);
}

.error-code {
  margin: 0;
  color: #2563eb;
  font-size: 72px;
  font-weight: 800;
}

h1 {
  margin: 10px 0 14px;
  color: #1e293b;
}

.description {
  color: #64748b;
  line-height: 1.7;
}

.button-group {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 28px;
}

button {
  padding: 11px 18px;
  color: white;
  background-color: #2563eb;
  border: 1px solid #2563eb;
  border-radius: 7px;
  cursor: pointer;
}

button:hover {
  background-color: #1d4ed8;
}

.secondary-button {
  color: #334155;
  background-color: white;
  border-color: #94a3b8;
}

.secondary-button:hover {
  background-color: #f1f5f9;
}
</style>
