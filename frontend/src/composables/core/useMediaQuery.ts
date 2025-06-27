import { ref, computed, onMounted, onUnmounted } from 'vue'

export function useMediaQuery(query: string) {
  const matches = ref<boolean>(false)

  const update = () => {
    matches.value = window.matchMedia(query).matches
  }

  onMounted(() => {
    if (typeof window === 'undefined') return
    update()
    const mediaQuery = window.matchMedia(query)
    const handler = (event: MediaQueryListEvent) => {
      matches.value = event.matches
    }
    mediaQuery.addEventListener('change', handler)
    onUnmounted(() => {
      mediaQuery.removeEventListener('change', handler)
    })
  })

  return { matches }
}

interface Breakpoints {
  xs: number
  sm: number
  md: number
  lg: number
  xl: number
}

const BREAKPOINTS: Breakpoints = {
  xs: 0,
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280
}

export function useBreakpoints() {
  const width = ref<number>(typeof window !== 'undefined' ? window.innerWidth : 0)
  const height = ref<number>(typeof window !== 'undefined' ? window.innerHeight : 0)

  const updateSize = () => {
    width.value = window.innerWidth
    height.value = window.innerHeight
  }

  onMounted(() => {
    if (typeof window === 'undefined') return
    window.addEventListener('resize', updateSize)
  })

  onUnmounted(() => {
    if (typeof window === 'undefined') return
    window.removeEventListener('resize', updateSize)
  })

  const isMobile = computed(() => width.value < BREAKPOINTS.md)
  const isTablet = computed(() => width.value >= BREAKPOINTS.md && width.value < BREAKPOINTS.lg)
  const isDesktop = computed(() => width.value >= BREAKPOINTS.lg)

  return {
    width,
    height,
    isMobile,
    isTablet,
    isDesktop
  }
} 