<template>
  <el-button
    :type="type"
    :size="size"
    :icon="icon"
    :loading="loading"
    :disabled="disabled"
    v-bind="$attrs"
    class="app-button"
  >
    <slot />
  </el-button>
</template>

<script setup lang="ts" name="AppButton">
import type { ButtonType, ButtonSize } from 'element-plus'

interface Props {
  type?: ButtonType
  size?: ButtonSize
  icon?: string | object
  loading?: boolean
  disabled?: boolean
}

withDefaults(defineProps<Props>(), {
  type: 'primary',
  size: 'default',
  loading: false,
  disabled: false
})
</script>

<style scoped>
.app-button {
  display: inline-flex;
  align-items: center;
}
</style>
