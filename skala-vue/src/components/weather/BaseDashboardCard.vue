<script setup>
// 공통 카드에 표시할 제목과 아이콘
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
  padding: 20px;
  background-color: white;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
}

.dashboard-title {
  display: flex;
  gap: 8px;
  align-items: center;
  margin: 0 0 16px;
  padding-bottom: 12px;
  color: #334155;
  font-size: 20px;
  border-bottom: 1px solid #e2e8f0;
}

.dashboard-content {
  width: 100%;
}
</style>
