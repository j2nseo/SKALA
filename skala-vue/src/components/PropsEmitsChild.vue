<script setup>
// 상위 컴포넌트에서 전달하는 메시지
defineProps({
  parentData: {
    type: String,
    required: true,
  },
})

// 메시지 갱신을 요청하는 사용자 이벤트
const emit = defineEmits(['update-request'])

// 버튼 클릭 시 새 메시지를 이벤트 데이터로 전달한다.
const sendNotification = () => {
  const payload = 'Child에서 가공한 새로운 데이터'

  // 이벤트 이름과 변경할 값을 함께 전달한다.
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
