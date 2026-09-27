<template>
  <el-button :icon="ArrowLeft" plain class="back-btn" @click="goBack">{{ text }}</el-button>
</template>

<script setup>
import { ArrowLeft } from '@element-plus/icons-vue'

const props = defineProps({
  text: { type: String, default: '返回' },
  // 没有上一页历史（如直接刷新子页）时跳转的兜底页面
  fallback: { type: String, default: '' },
})

function goBack() {
  uni.navigateBack({
    fail: () => {
      if (props.fallback) uni.redirectTo({ url: props.fallback })
    },
  })
}
</script>

<style>
.back-btn {
  font-weight: 500;
}
</style>
