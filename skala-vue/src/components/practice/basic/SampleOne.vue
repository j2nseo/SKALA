<script setup>
import { ref } from 'vue'

let normalCount = 0
const vueCount = ref(0)
</script>

<template>
  <div class="practice-section">
    <h2>hello Skala-vue</h2>
    <h3>일반 변수 클릭 : {{ normalCount }}</h3>
    <button @click="normalCount++">일반 변수 클릭</button>
    <br />
    <h3>ref 변수 클릭 : {{ vueCount }}</h3>
    <button @click="vueCount++">vue 변수 클릭</button>
  </div>
</template>
