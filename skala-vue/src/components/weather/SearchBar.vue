<script setup>
// 부모 컴포넌트로부터 검색어를 받습니다.
defineProps({
  query: {
    type: String,
    required: true,
  },
})

// 부모에게 보낼 이벤트를 등록합니다.
const emit = defineEmits(['update-query'])

// 입력창의 값이 바뀔 때 실행됩니다.
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
