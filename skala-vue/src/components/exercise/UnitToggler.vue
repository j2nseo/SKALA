<script setup>
import { useConfigStore } from '../../stores/configStore'

const configStore = useConfigStore()
</script>

<template>
  <el-button class="unit-toggler" size="small" type="warning" @click="configStore.toggleUnit">
    {{ configStore.unitSymbol }} 단위로 보기
  </el-button>
</template>

<style scoped>
.unit-toggler {
  padding: 8px 11px;
  font-size: 13px;
  font-weight: 800;
}
</style>
