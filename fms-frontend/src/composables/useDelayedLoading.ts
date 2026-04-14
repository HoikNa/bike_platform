import { ref, watch } from "vue"

/**
 * 로딩 상태를 지연 표시하는 컴포저블.
 *
 * 300ms 미만의 API 응답에서 Skeleton UI 깜빡임을 방지합니다.
 *
 * @param source  isLoading 상태를 반환하는 getter 함수
 * @param delay   Skeleton 표시 지연 시간 (ms, 기본 300)
 *
 * @example
 * const { showLoading } = useDelayedLoading(() => isLoading.value)
 */
export function useDelayedLoading(source: () => boolean, delay = 300) {
  const showLoading = ref(false)
  let timer: ReturnType<typeof setTimeout> | null = null

  watch(
    source,
    (loading) => {
      if (loading) {
        timer = setTimeout(() => { showLoading.value = true }, delay)
      } else {
        if (timer) clearTimeout(timer)
        showLoading.value = false
      }
    },
    { immediate: true }
  )

  return { showLoading }
}
