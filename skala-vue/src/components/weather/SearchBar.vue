<script setup>
// 검색창에 표시할 검색어
defineProps({
  query: {
    type: String,
    required: true,
  },
})

// 입력값 변경을 전달하는 이벤트
const emit = defineEmits(['update-query'])

const handleInput = (event) => {
  emit('update-query', event.target.value)
}
</script>

<template>
  <div class="search-area">
    <input type="text" :value="query" placeholder="검색할 도시 이름 입력" @input="handleInput" />

    <p>
      검색 중인 도시:
      <strong>{{ query || '없음' }}</strong>
    </p>
  </div>
</template>

<style scoped>
.search-area input {
  box-sizing: border-box;
  width: 100%;
  padding: 12px 14px;
  font-size: 16px;
  border: 1px solid #94a3b8;
  border-radius: 6px;
  outline: none;
}

.search-area input:focus {
  border-color: #2563eb;
}

.search-area p {
  margin: 12px 0 0;
  color: #475569;
}

.search-area strong {
  color: #2563eb;
}
</style>
