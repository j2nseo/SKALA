<script setup>
import { ref } from 'vue'
import PropsEmitsChild from './PropsEmitsChild.vue'

// 부모 컴포넌트가 소유한 반응형 데이터
const message = ref('Parent 초기 메시지')

// 자식의 update-request 이벤트가 발생하면 실행되는 함수
const handleUpdateRequest = (newValue) => {
  // 자식이 보낸 데이터를 부모의 message에 저장
  message.value = newValue
}
</script>

<template>
  <div class="practice-section">
    <h1>Props & Emits 실습</h1>

    <div class="parent-container">
      <h2>상위 컴포넌트 (Parent)</h2>

      <p>
        현재 부모 데이터:
        <strong>{{ message }}</strong>
      </p>

      <!--
        Props:
        부모의 message를 자식의 parentData로 전달

        Emits:
        자식의 update-request 이벤트를 받으면
        handleUpdateRequest 함수 실행
      -->
      <PropsEmitsChild :parent-data="message" @update-request="handleUpdateRequest" />
    </div>
  </div>
</template>

<style scoped>
.practice-section {
  max-width: 700px;
  margin: 40px auto;
  padding: 32px;
  color: #1e293b;
  font-family: Arial, sans-serif;
}

.practice-section > h1 {
  margin-top: 0;
  margin-bottom: 24px;
  text-align: center;
  color: #0f172a;
}

.parent-container {
  padding: 24px;
  background-color: #f8fafc;
  border: 2px solid #64748b;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.1);
}

.parent-container > h2 {
  margin-top: 0;
  color: #334155;
}

.parent-container > p {
  line-height: 1.7;
}

.parent-container > p strong {
  color: #dc2626;
}
</style>
