<script setup>
// 입력창에 표시할 검색어
defineProps({
  query: {
    type: String,
    required: true,
  },
})

// 입력 변경과 검색 실행을 구분한 이벤트
const emit = defineEmits(['update-query', 'search-city'])

const handleInput = (event) => {
  emit('update-query', event.target.value)
}

const handleSubmit = () => {
  emit('search-city')
}
</script>

<template>
  <form class="search-area" @submit.prevent="handleSubmit">
    <div class="search-input-row">
      <input
        type="text"
        :value="query"
        placeholder="예) 수원, 대구, 강릉, San Diego, Nice"
        @input="handleInput"
      />
      <button type="submit">검색</button>
    </div>

    <p>
      검색 중인 도시:
      <strong>{{ query || '없음' }}</strong>
    </p>
  </form>
</template>

<style scoped>
.search-area input {
  box-sizing: border-box;
  width: 100%;
  padding: 14px 16px;
  font-size: 16px;
  color: #302e48;
  background: #faf9ff;
  border: 1px solid #e4e0f5;
  border-radius: 10px;
  outline: none;
}

.search-input-row {
  display: flex;
  gap: 8px;
}

.search-input-row button {
  flex: 0 0 auto;
  padding: 0 18px;
  color: white;
  font-weight: 700;
  background: #7c3aed;
  border: 0;
  border-radius: 10px;
  cursor: pointer;
}

.search-area input:focus {
  background: white;
  border-color: #8b5cf6;
  box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.12);
}

.search-area p {
  margin: 12px 0 0;
  color: #475569;
}

.search-area strong {
  color: #7c3aed;
}
</style>
