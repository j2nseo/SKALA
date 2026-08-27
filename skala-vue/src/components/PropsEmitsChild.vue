<script setup>
// 부모 컴포넌트로부터 받을 데이터 정의
defineProps({
  parentData: {
    type: String,
    required: true,
  },
})

// 부모 컴포넌트에 보낼 이벤트 정의
const emit = defineEmits(['update-request'])

// 버튼을 클릭하면 실행되는 함수
const sendNotification = () => {
  const payload = 'Child에서 가공한 새로운 데이터'

  // 부모에게 이벤트와 데이터를 함께 전달
  emit('update-request', payload)
}
</script>

<template>
  <div class="child-container">
    <h2>하위 컴포넌트 (Child)</h2>

    <p>
      수신된 Props 데이터:
      <strong>{{ parentData }}</strong>
    </p>

    <button @click="sendNotification">상위 컴포넌트로 갱신 요청 (Emit)</button>
  </div>
</template>

<style scoped>
.child-container {
  margin-top: 24px;
  padding: 24px;
  background-color: #eff6ff;
  border: 2px solid #60a5fa;
  border-radius: 12px;
}

.child-container h2 {
  margin-top: 0;
  color: #1d4ed8;
}

.child-container p {
  line-height: 1.7;
}

.child-container strong {
  color: #dc2626;
}

button {
  padding: 10px 16px;
  color: white;
  font-size: 14px;
  background-color: #2563eb;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

button:hover {
  background-color: #1d4ed8;
}
</style>
