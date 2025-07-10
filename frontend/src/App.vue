<script setup lang="ts">
import { RouterView } from 'vue-router'
import { useUIStore } from '@/stores/modules/ui'
import { computed } from 'vue'

const uiStore = useUIStore()
const isDarkMode = computed(() => uiStore.isDarkMode)
</script>

<template>
  <div id="app-wrapper" :class="{ 'dark': isDarkMode }">
    <RouterView />
  </div>
</template>

<style lang="scss">
#app-wrapper {
  width: 100%;
  height: 100%;
  overflow: hidden;
}
</style>
