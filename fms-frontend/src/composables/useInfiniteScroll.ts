import { ref, onMounted, onUnmounted } from "vue"

/**
 * IntersectionObserver 기반 무한 스크롤 컴포저블.
 *
 * @param callback  하단 트리거 감지 시 실행할 함수 (다음 페이지 로드)
 * @param threshold 트리거 임계값 (기본 0.1 = 10% 노출 시)
 *
 * @example
 * const { sentinelRef } = useInfiniteScroll(loadMore)
 * // template: <div ref="sentinelRef" />
 */
export function useInfiniteScroll(callback: () => void, threshold = 0.1) {
  const sentinelRef = ref<HTMLElement | null>(null)
  let observer: IntersectionObserver | null = null

  onMounted(() => {
    if (!sentinelRef.value) return
    observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) callback()
      },
      { threshold }
    )
    observer.observe(sentinelRef.value)
  })

  onUnmounted(() => {
    observer?.disconnect()
  })

  return { sentinelRef }
}
