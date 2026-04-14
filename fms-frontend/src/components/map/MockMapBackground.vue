<template>
  <!--
    서울 중심권 목업 지도 (126.85°E–127.15°E / 37.45°N–37.65°N)
    viewBox 0–100 좌표 = lngToX / latToY 함수와 동일한 좌표계
    preserveAspectRatio="none" → 컨테이너를 꽉 채움
    vector-effect="non-scaling-stroke" → 도로 선폭이 항상 일정한 px
  -->
  <svg
    class="absolute inset-0 w-full h-full pointer-events-none"
    viewBox="0 0 100 100"
    preserveAspectRatio="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <!-- ══ 1. 배경 (토지) ══════════════════════════════════════ -->
    <rect width="100" height="100" :fill="c.land" />

    <!-- ══ 2. 공원 / 녹지 ═════════════════════════════════════ -->
    <!-- 북한산 (북부) -->
    <ellipse cx="42" cy="10" rx="16" ry="9"  :fill="c.park" />
    <!-- 관악산 (남부) -->
    <ellipse cx="28" cy="91" rx="11" ry="8"  :fill="c.park" />
    <!-- 남산 (중부) -->
    <ellipse cx="44" cy="56" rx="5"  ry="4"  :fill="c.park" />
    <!-- 올림픽공원 -->
    <rect    x="76"  y="70" width="8" height="6" rx="1" :fill="c.park" />
    <!-- 서울숲 (성수) -->
    <rect    x="64"  y="52" width="5" height="4" rx="1" :fill="c.park" />

    <!-- ══ 3. 한강 ════════════════════════════════════════════ -->
    <!--
      북안: ~37.535°N (y≈57.5), 남안: ~37.515°N (y≈67.5)
      중심선: y≈62, 폭: 약 5 SVG 단위
    -->
    <path
      d="M -1,58  C 15,56  30,58  42,61
                  C 52,64  65,62  80,59
                  C 90,57  95,58  101,58
         L 101,64
                  C 95,63  90,63  80,64
                  C 65,67  52,69  42,66
                  C 30,63  15,62  -1,63 Z"
      :fill="c.river"
    />

    <!-- ══ 4. 한강 교량 (16개) ════════════════════════════════ -->
    <!--
      각 교량은 북안(y≈58)–남안(y≈64) 사이 수직선
      svg x = lngToX(경도) = (경도 - 126.85) / 0.30 * 100
    -->
    <g :stroke="c.bridge" stroke-width="0.5" vector-effect="non-scaling-stroke">
      <!-- 행주대교  lng=126.864 → x=4.7  -->  <line x1="4.7"  y1="57" x2="4.7"  y2="64" />
      <!-- 방화대교  lng=126.883 → x=11   -->  <line x1="11"   y1="57" x2="11"   y2="64" />
      <!-- 마곡대교  lng=126.873 → x=7.7  -->  <line x1="7.7"  y1="57" x2="7.7"  y2="64" />
      <!-- 가양대교  lng=126.875 → x=8.3  -->  <line x1="8.3"  y1="57" x2="8.3"  y2="64" />
      <!-- 성산대교  lng=126.908 → x=19.3 -->  <line x1="19.3" y1="57" x2="19.3" y2="64" />
      <!-- 마포대교  lng=126.944 → x=31.3 -->  <line x1="31.3" y1="57" x2="31.3" y2="64" />
      <!-- 원효대교  lng=126.963 → x=37.7 -->  <line x1="37.7" y1="57" x2="37.7" y2="64" />
      <!-- 한강대교  lng=126.989 → x=46.3 -->  <line x1="46.3" y1="57" x2="46.3" y2="64" />
      <!-- 반포대교  lng=127.005 → x=51.7 -->  <line x1="51.7" y1="57" x2="51.7" y2="64" />
      <!-- 동호대교  lng=127.014 → x=54.7 -->  <line x1="54.7" y1="57" x2="54.7" y2="64" />
      <!-- 성수대교  lng=127.045 → x=65   -->  <line x1="65"   y1="57" x2="65"   y2="64" />
      <!-- 영동대교  lng=127.063 → x=71   -->  <line x1="71"   y1="57" x2="71"   y2="64" />
      <!-- 청담대교  lng=127.063 → x=71   -->  <!-- merged with 영동 -->
      <!-- 잠실대교  lng=127.083 → x=77.7 -->  <line x1="77.7" y1="57" x2="77.7" y2="64" />
      <!-- 천호대교  lng=127.109 → x=86.3 -->  <line x1="86.3" y1="57" x2="86.3" y2="64" />
      <!-- 광진교    lng=127.121 → x=90.3 -->  <line x1="90.3" y1="57" x2="90.3" y2="64" />
    </g>

    <!-- ══ 5. 고속화도로 (두꺼운 선, 노란/주황계열) ═══════════ -->
    <g :stroke="c.expressway" stroke-width="1.4" fill="none" vector-effect="non-scaling-stroke"
       stroke-linecap="round" stroke-linejoin="round">
      <!-- 강변북로 (한강 북안 평행, y≈55) -->
      <path d="M -1,55  C 15,53  30,55  42,58
                        C 52,61  65,59  80,56
                        C 90,54  95,55  101,55" />
      <!-- 올림픽대로 (한강 남안 평행, y≈66) -->
      <path d="M -1,66  C 15,64  30,66  42,69
                        C 52,72  65,70  80,67
                        C 90,65  95,66  101,66" />
      <!-- 내부순환도로 -->
      <path d="M 17,47  C 17,28  32,19  45,19
                        C 60,19  67,30  67,46
                        C 67,60  58,68  45,69
                        C 30,70  17,62  17,47" />
      <!-- 경부고속도로 (남북 관통, Gangnam축) -->
      <path d="M 59,48  L 58,75  L 56,100" />
      <!-- 동부간선도로 -->
      <path d="M 80,5   L 78,72" />
      <!-- 서부간선도로 -->
      <path d="M 9,28   L 10,80" />
      <!-- 북부간선도로 -->
      <path d="M 35,23  L 78,20" />
      <!-- 남부순환로 -->
      <path d="M 18,81  L 75,81" />
    </g>

    <!-- ══ 6. 간선도로 (중간 굵기) ═══════════════════════════ -->
    <g :stroke="c.arterial" stroke-width="0.7" fill="none" vector-effect="non-scaling-stroke"
       stroke-linecap="round" stroke-linejoin="round">
      <!-- 종로 (동서, y≈33) -->
      <line x1="28" y1="33" x2="65" y2="33" />
      <!-- 을지로 -->
      <line x1="29" y1="37.5" x2="64" y2="37.5" />
      <!-- 퇴계로 -->
      <line x1="28" y1="42" x2="62" y2="44" />
      <!-- 테헤란로 (Gangnam 동서, y≈76) -->
      <line x1="48" y1="76" x2="80" y2="76" />
      <!-- 강남대로 (남북, x≈58) -->
      <line x1="58" y1="50" x2="58" y2="85" />
      <!-- 미아사거리~신촌 (대각선) -->
      <path d="M 24,47  L 36,38  L 42,35" />
      <!-- 성수대교북단~광화문 -->
      <path d="M 65,52  L 58,40  L 50,35" />
      <!-- 청담~삼성 -->
      <line x1="69" y1="60" x2="70" y2="75" />
    </g>

    <!-- ══ 7. 보조 도로 (얇은 선) ════════════════════════════ -->
    <g :stroke="c.road" stroke-width="0.35" fill="none" vector-effect="non-scaling-stroke"
       stroke-linecap="round">
      <!-- 홍대~합정 -->
      <line x1="21" y1="47" x2="28" y2="53" />
      <!-- 이태원~한남 -->
      <line x1="39" y1="62" x2="46" y2="65" />
      <!-- 잠실~석촌 -->
      <line x1="80" y1="65" x2="82" y2="72" />
      <!-- 노원 방사선 -->
      <path d="M 62,15  L 68,25  L 70,35" />
      <!-- 망원~여의도 -->
      <path d="M 15,52  L 22,57  L 26,64" />
      <!-- 여의도 순환 -->
      <ellipse cx="27" cy="67" rx="5" ry="3" fill="none" />
      <!-- 분당선 방향 (동남) -->
      <path d="M 66,76  L 72,82  L 76,88" />
      <!-- 구로방향 -->
      <path d="M 14,72  L 16,80  L 20,88" />
    </g>

    <!-- ══ 8. 지역 라벨 ══════════════════════════════════════ -->
    <!--
      글자 크기는 SVG 단위이므로 preserveAspectRatio=none에서 왜곡될 수 있음.
      실제 표시는 RealtimeMap.vue의 CSS 라벨이 담당하므로 여기서는 생략.
    -->

  </svg>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from "vue"

// ── 다크모드 감지 (MutationObserver) ──────────────────────────
const isDark = ref(false)
let observer: MutationObserver | null = null

onMounted(() => {
  isDark.value = document.documentElement.classList.contains("dark")
  observer = new MutationObserver(() => {
    isDark.value = document.documentElement.classList.contains("dark")
  })
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] })
})
onUnmounted(() => observer?.disconnect())

// ── 라이트 / 다크 색상 팔레트 ─────────────────────────────────
const c = computed(() => isDark.value
  ? {
      land:       "#1b2333",  // 다크 네이비
      park:       "#1a3a28",  // 다크 그린
      river:      "#1a3a5c",  // 다크 블루
      bridge:     "#2a4060",
      expressway: "#3a4a5a",
      arterial:   "#2c3a48",
      road:       "#243040",
    }
  : {
      land:       "#f2ece0",  // 따뜻한 베이지 (OSM 스타일)
      park:       "#c8e6b8",  // 연한 초록
      river:      "#aad4f0",  // 연한 하늘색
      bridge:     "#d4c8b0",
      expressway: "#f5d060",  // 한국 고속도로 특유의 노란색
      arterial:   "#e8ddd0",
      road:       "#ede6da",
    }
)
</script>
