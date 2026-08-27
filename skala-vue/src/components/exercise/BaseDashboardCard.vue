<script setup>
// 여러 대시보드 영역에서 공통으로 사용하는 제목과 아이콘
defineProps({
  icon: {
    type: String,
    default: '',
  },

  title: {
    type: String,
    required: true,
  },
})
</script>

<template>
  <section class="dashboard-card">
    <h2 class="dashboard-title">
      <span>{{ icon }}</span>
      {{ title }}
    </h2>

    <div class="dashboard-content">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.dashboard-card {
  margin-bottom: 20px;
  padding: 24px;
  background: white;
  border: 1px solid #eceaf5;
  border-radius: 16px;
  box-shadow: 0 8px 22px rgba(58, 44, 116, 0.06);
}

.dashboard-title {
  display: flex;
  gap: 8px;
  align-items: center;
  margin: 0 0 16px;
  padding-bottom: 12px;
  color: #302e48;
  font-size: 19px;
  border-bottom: 1px solid #e2e8f0;
}

.dashboard-content {
  width: 100%;
}
</style>
