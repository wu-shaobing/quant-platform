<template>
  <div :class="['app-card', shadowClass]">
    <header v-if="title || $slots.header" class="app-card-header">
      <h3 v-if="title">{{ title }}</h3>
      <slot name="header" />
    </header>
    <section class="app-card-body">
      <slot />
    </section>
    <footer v-if="$slots.footer" class="app-card-footer">
      <slot name="footer" />
    </footer>
  </div>
</template>

<script setup lang="ts" name="AppCard">
import { computed } from 'vue'

interface Props {
  title?: string
  shadow?: 'always' | 'hover' | 'never'
}

const props = withDefaults(defineProps<Props>(), {
  shadow: 'hover'
})

const shadowClass = computed(() => {
  switch (props.shadow) {
    case 'always':
      return 'app-card-shadow'
    case 'hover':
      return 'app-card-shadow-hover'
    case 'never':
    default:
      return ''
  }
})
</script>

<style scoped>
.app-card {
  background: #fff;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.2s ease;
}

.app-card-shadow {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.app-card-shadow-hover:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.app-card-header {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.app-card-body {
  padding: 16px;
  flex: 1;
}

.app-card-footer {
  padding: 12px 16px;
  border-top: 1px solid #f0f0f0;
}
</style>
