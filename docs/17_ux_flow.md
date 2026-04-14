# 17. UX Flow — 사용자 경험 및 예외 처리 흐름도

> **대상 화면**: 관제 대시보드 (Web) + 모바일 앱 (App)  
> **원칙**: 모든 비동기 상태(로딩, 에러, 빈 결과)에 대해 명시적인 UX 분기를 정의합니다.

---

## 목차

1. [Flow 1 — 로그인 및 토큰 생명주기](#flow-1--로그인-및-토큰-생명주기)
2. [Flow 2 — 관제 대시보드 진입 및 차량 선택](#flow-2--관제-대시보드-진입-및-차량-선택)
3. [Flow 3 — 차량 상세 및 센서 이력 조회](#flow-3--차량-상세-및-센서-이력-조회)
4. [Flow 4 — 알림 목록 및 처리 (무한 스크롤)](#flow-4--알림-목록-및-처리)
5. [Flow 5 — 배터리 교체 권고 (모바일 앱)](#flow-5--배터리-교체-권고-모바일-앱)
6. [예외 처리 UX 공통 가이드](#예외-처리-ux-공통-가이드)
   - 6.1 API 응답 지연 — Skeleton UI
   - 6.2 인증 토큰 만료 — 자동 갱신 및 만료 모달
   - 6.3 빈 결과 — Empty State 디자인

---

## Flow 1 — 로그인 및 토큰 생명주기

```mermaid
flowchart TD
    START(["앱 진입 (URL 접속)"])
    START --> CHECK_TOKEN{"localStorage에\naccess_token 있음?"}

    CHECK_TOKEN -- "없음" --> LOGIN_PAGE["로그인 페이지\n/login 렌더링"]
    CHECK_TOKEN -- "있음" --> FETCH_ME["GET /auth/me 호출\n(currentUser 복원)"]

    FETCH_ME --> ME_OK{"200 OK?"}
    ME_OK -- "성공" --> RESTORE["currentUser 복원 완료\n요청했던 페이지로 이동"]
    ME_OK -- "401 (토큰 만료)" --> TRY_REFRESH["POST /auth/refresh 호출\n(HttpOnly 쿠키)"]

    TRY_REFRESH --> REFRESH_OK{"200 OK?"}
    REFRESH_OK -- "성공" --> RETRY_ME["GET /auth/me 재호출"]
    RETRY_ME --> RESTORE
    REFRESH_OK -- "401 (RefreshToken 만료)" --> FORCE_LOGOUT["localStorage 초기화\n/login 리다이렉트"]

    LOGIN_PAGE --> INPUT["이메일 · 비밀번호 입력"]
    INPUT --> SUBMIT["로그인 버튼 클릭"]
    SUBMIT --> LOGIN_LOADING["버튼 Spinner\n+ 필드 disabled"]

    LOGIN_LOADING --> LOGIN_API["POST /auth/login"]
    LOGIN_API --> LOGIN_OK{"200 OK?"}

    LOGIN_OK -- "성공" --> SAVE_TOKEN["accessToken → localStorage\nRefreshToken → Set-Cookie(HttpOnly)"]
    SAVE_TOKEN --> REDIRECT["요청 경로 or /app/dashboard 이동"]
    REDIRECT --> WS_CONNECT["useRealtimeStore.connect()\nWebSocket 연결"]

    LOGIN_OK -- "401 INVALID_CREDENTIALS" --> SHOW_ERR["인라인 에러 메시지\n'이메일 또는 비밀번호가 올바르지 않습니다.'"]
    SHOW_ERR --> INPUT

    LOGIN_OK -- "400 VALIDATION_ERROR" --> FIELD_ERR["각 입력 필드 하단\n에러 메시지 표시"]
    FIELD_ERR --> INPUT

    LOGIN_OK -- "500" --> TOAST_ERR["Toast 에러\n'서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'"]
    TOAST_ERR --> INPUT
```

---

## Flow 2 — 관제 대시보드 진입 및 차량 선택

```mermaid
flowchart TD
    ENTER(["authGuard 통과\n/app/dashboard 진입"])
    ENTER --> PARALLEL_LOAD

    subgraph PARALLEL_LOAD["병렬 데이터 로드 (Promise.all)"]
        L1["useFleetStore.fetchVehicles()"]
        L2["useAlertStore.fetchAlerts({is_acknowledged:false})"]
    end

    PARALLEL_LOAD --> LOADING_STATE["화면 상태: Skeleton UI 표시\nKPI 카드 × 4\n차량 리스트\n알림 목록"]

    LOADING_STATE --> LOAD_DONE{"로드 완료?"}

    LOAD_DONE -- "성공" --> RENDER_DASH["대시보드 렌더링\n- KPI 카드 (운행중/경고/오프라인)\n- 지도 (실시간 오토바이 아이콘)\n- 차량 현황 패널\n- 미확인 알림 목록"]

    LOAD_DONE -- "실패 (네트워크)" --> DASH_ERR["Toast 경고\n'데이터 로드에 실패했습니다. 새로고침을 시도합니다.'\n+ 재시도 버튼"]

    RENDER_DASH --> WS_LISTEN["WebSocket 이벤트 수신 시작\nVEHICLE_LOCATION_UPDATE → 지도 아이콘 이동\nALERT_TRIGGERED → 알림 목록 최상단 삽입 + Toast"]

    RENDER_DASH --> FILTER["차량 상태 필터 변경\n(전체 / 운행중 / 경고 / 오프라인)"]
    FILTER --> FILTER_API["GET /vehicles?status=..."]
    FILTER_API --> FILTER_RESULT{"결과 있음?"}
    FILTER_RESULT -- "items.length > 0" --> UPDATE_LIST["차량 목록 업데이트"]
    FILTER_RESULT -- "items.length === 0" --> EMPTY_VEHICLES["Empty State\n빈 차량 아이콘 + '해당 조건의 차량이 없습니다.'"]

    RENDER_DASH --> SELECT_VEHICLE["차량 카드 / 지도 아이콘 클릭"]
    SELECT_VEHICLE --> NAV_DETAIL["router.push('/app/vehicles/:id')"]
```

---

## Flow 3 — 차량 상세 및 센서 이력 조회

```mermaid
flowchart TD
    ENTER(["VehicleDetailView 진입\n/app/vehicles/:vehicleId"])
    ENTER --> PARALLEL

    subgraph PARALLEL["병렬 API 호출"]
        D1["GET /vehicles/{id}\n차량 상세 + 최신 센서"]
        D2["GET /vehicles/{id}/sensors\n센서 이력 첫 페이지\n(limit=50)"]
        D3["GET /vehicles/{id}/trips?status=active\n진행 중 운행 조회"]
    end

    PARALLEL --> SKELETON["Skeleton UI\n- 차량 정보 카드\n- 배터리 게이지\n- 지도\n- 센서 그래프"]

    SKELETON --> DETAIL_DONE{"로드 완료?"}

    DETAIL_DONE -- "성공" --> RENDER_DETAIL["상세 화면 렌더링\n- 번호판 / 상태 배지\n- BatteryGauge\n- 지도 (현재 위치 마커)\n- 센서 이력 그래프"]

    DETAIL_DONE -- "404 VEHICLE_NOT_FOUND" --> NOT_FOUND["안내 모달\n'차량을 찾을 수 없습니다. 삭제됐거나 권한이 없는 차량입니다.'\n+ 목록으로 이동 버튼"]
    NOT_FOUND --> BACK["router.push('/app/vehicles')"]

    DETAIL_DONE -- "403 FORBIDDEN" --> FORBIDDEN["Toast 에러\n'이 차량에 접근할 권한이 없습니다.'"]
    FORBIDDEN --> BACK

    RENDER_DETAIL --> SUBSCRIBE_WS["useRealtimeStore.subscribe([vehicleId])\nVEHICLE_LOCATION_UPDATE → 마커 실시간 이동"]

    RENDER_DETAIL --> SCROLL_SENSOR["센서 이력 스크롤 아래로"]
    SCROLL_SENSOR --> INTERSECT{"IntersectionObserver\n하단 트리거 감지?"}
    INTERSECT -- "아직 위" --> INTERSECT
    INTERSECT -- "하단 도달 + has_next=true" --> LOAD_MORE["GET /vehicles/{id}/sensors\n?cursor={next_cursor}"]
    LOAD_MORE --> APPEND["센서 이력 목록 하단 추가"]
    APPEND --> INTERSECT

    INTERSECT -- "has_next=false" --> END_MSG["'모든 기록을 불러왔습니다.' 표시"]

    RENDER_DETAIL --> LEAVE["페이지 이탈 (뒤로가기 / 다른 메뉴)"]
    LEAVE --> UNSUB["useRealtimeStore.unsubscribe([vehicleId])"]
    UNSUB --> CLEAR["useFleetStore.clearSelectedVehicle()"]
```

---

## Flow 4 — 알림 목록 및 처리

```mermaid
flowchart TD
    ENTER(["AlertListView 진입\n/app/alerts"])
    ENTER --> FILTER_UI["필터 칩 표시\n전체 / 위험 / 주의 / 정보\n/ 미확인만"]

    FILTER_UI --> LOAD["useAlertStore.fetchAlerts()\n첫 페이지 로드 (limit=30)"]
    LOAD --> SKELETON["목록 Skeleton\n(AlertListItem × 5)"]

    SKELETON --> LOAD_DONE{"로드 완료?"}
    LOAD_DONE -- "성공 + items.length > 0" --> RENDER_LIST["알림 목록 렌더링\n미확인 = 파란 dot + 배경 강조\n심각도별 아이콘 색상"]
    LOAD_DONE -- "성공 + items.length === 0" --> EMPTY_ALERT["Empty State\n알림 아이콘 + '현재 알림이 없습니다.'"]
    LOAD_DONE -- "실패" --> ERROR_ALERT["Toast 에러\n+ 재시도 버튼"]

    RENDER_LIST --> SCROLL_DOWN["목록 하단으로 스크롤"]
    SCROLL_DOWN --> IO{"IntersectionObserver?"}
    IO -- "하단 도달 + has_next=true" --> LOAD_MORE_SPINNER["인라인 스피너 표시\n(하단에 작은 로딩 점)"]
    LOAD_MORE_SPINNER --> LOAD_MORE["useAlertStore.loadMore()\n?cursor={next_cursor}"]
    LOAD_MORE --> APPEND["기존 목록 하단에 추가"]
    APPEND --> IO

    RENDER_LIST --> CLICK_ITEM["알림 아이템 클릭"]
    CLICK_ITEM --> SHOW_DETAIL["AlertAcknowledgeModal 열기\n- 알림 상세 정보\n- 발생 위치 미니맵\n- 확인 처리 버튼"]

    SHOW_DETAIL --> ACK_CLICK{"'확인 처리' 버튼?"}
    ACK_CLICK -- "클릭" --> ACK_API["PATCH /alerts/{id}/acknowledge"]
    ACK_API --> ACK_OK{"성공?"}
    ACK_OK -- "성공" --> UPDATE_ITEM["목록 내 해당 아이템\n미확인 dot 제거 + 배경색 변경"]
    UPDATE_ITEM --> CLOSE_MODAL["모달 닫기"]
    ACK_OK -- "실패" --> TOAST_ACK_ERR["Toast 에러\n'처리 중 오류가 발생했습니다.'"]
    TOAST_ACK_ERR --> SHOW_DETAIL

    RENDER_LIST --> REALTIME_INSERT["WebSocket ALERT_TRIGGERED 수신\n→ useAlertStore.prependAlert()\n→ 목록 최상단 애니메이션 삽입"]
```

---

## Flow 5 — 배터리 교체 권고 (모바일 앱)

```mermaid
flowchart TD
    WS_EVENT(["WebSocket\nBATTERY_REPLACE_REQUIRED 이벤트 수신"])
    WS_EVENT --> FOREGROUND{"앱이 포그라운드?"}

    FOREGROUND -- "포그라운드" --> OPEN_MODAL["useUIStore.openBatteryModal(payload)\n배터리 교체 권고 바텀시트 열기"]

    FOREGROUND -- "백그라운드" --> FCM["FCM Push 알림 발송\n제목: '배터리 교체 권고'\n본문: '잔량 22% — 35분 내 방전 예상'"]
    FCM --> TAP_NOTIF{"알림 탭?"}
    TAP_NOTIF -- "탭함" --> OPEN_APP["앱 포그라운드 전환\n+ OPEN_MODAL"]
    TAP_NOTIF -- "무시" --> DISMISS["알림 무시됨"]

    OPEN_MODAL --> MODAL_CONTENT["바텀시트 콘텐츠\n⚡ 배터리 잔량: 22%\n⏱ 예상 방전: 35분 후\n\n가까운 충전소 목록 (최대 3개)\n[0.87km] 강남 FMS 충전소 1호점 — 슬롯 3개\n[1.24km] 역삼 FMS 충전소 2호점 — 슬롯 1개"]

    MODAL_CONTENT --> USER_ACTION{"사용자 액션?"}

    USER_ACTION -- "충전소 선택" --> DEEPLINK["내비게이션 앱 딥링크 실행\nkakaonavi://navigate?...\n또는 T맵 URI"]
    DEEPLINK --> NAV_APP["외부 내비게이션 앱 실행\n목적지: 충전소 위치"]
    NAV_APP --> UPDATE_VEHICLE["차량 상태 업데이트\nVehicleStatus → CHARGING (서버 수신 시)"]

    USER_ACTION -- "나중에" --> DISMISS_MODAL["바텀시트 닫기\n5분 후 Toast 재알림 예약"]

    USER_ACTION -- "더 많은 충전소 보기" --> STATION_API["GET /charging-stations\n?lat={lat}&lng={lng}&radius_km=5"]
    STATION_API --> STATION_LIST["전체 충전소 목록\n거리순 정렬"]
    STATION_LIST --> USER_ACTION
```

---

## 예외 처리 UX 공통 가이드

### 6.1 API 응답 지연 — Skeleton UI

**원칙**: 로딩 상태는 즉시 표시하되, 300ms 미만은 깜빡임을 방지하기 위해 스켈레톤을 지연 표시합니다.

```typescript
// src/composables/useDelayedLoading.ts
import { ref, watch } from "vue"

/**
 * 로딩 상태를 지연 표시하는 컴포저블.
 *
 * @param source  - isLoading ref 또는 getter 함수
 * @param delay   - 스켈레톤 표시 지연 시간 (ms, 기본 300)
 *
 * 동작:
 *   - 로딩 시작 → delay ms 후에 showLoading = true
 *   - 로딩 완료 → 즉시 showLoading = false (타이머 취소)
 *   - 300ms 이내에 완료되면 스켈레톤 UI가 전혀 보이지 않습니다.
 */
export function useDelayedLoading(source: () => boolean, delay = 300) {
  const showLoading = ref(false)
  let timer: ReturnType<typeof setTimeout> | null = null

  watch(source, (loading) => {
    if (loading) {
      timer = setTimeout(() => { showLoading.value = true }, delay)
    } else {
      if (timer) clearTimeout(timer)
      showLoading.value = false
    }
  }, { immediate: true })

  return { showLoading }
}
```

**컴포넌트 적용 예시**

```vue
<!-- VehicleListView.vue -->
<template>
  <div>
    <!-- 300ms 이상 로딩 시에만 스켈레톤 표시 -->
    <template v-if="showLoading">
      <BaseSkeleton v-for="i in 5" :key="i" class="h-20 rounded-lg mb-3" />
    </template>

    <!-- 로딩 완료 + 결과 있음 -->
    <template v-else-if="!isLoading && vehicles.length > 0">
      <VehicleListItem
        v-for="vehicle in vehicles"
        :key="vehicle.id"
        :vehicle="vehicle"
        @select="onSelectVehicle"
      />
    </template>

    <!-- 로딩 완료 + 결과 없음 -->
    <BaseEmptyState
      v-else-if="!isLoading && vehicles.length === 0"
      icon="TruckIcon"
      title="차량이 없습니다"
      description="등록된 차량이 없거나 검색 조건에 맞는 차량이 없습니다."
    />
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from "pinia"
import { useFleetStore } from "@/stores/fleet"
import { useDelayedLoading } from "@/composables/useDelayedLoading"

const fleetStore = useFleetStore()
const { vehicles, isListLoading: isLoading } = storeToRefs(fleetStore)
const { showLoading } = useDelayedLoading(() => isLoading.value)
</script>
```

**스켈레톤 디자인 규격**

| 컴포넌트 | 스켈레톤 크기 | 반복 수 |
|---|---|---|
| KPI 카드 (Stat Card) | `h-24 w-full rounded-lg` | 4개 |
| 차량 리스트 아이템 | `h-20 w-full rounded-lg` | 5개 |
| 알림 리스트 아이템 | `h-16 w-full rounded-md` | 5개 |
| 차량 상세 카드 | `h-40 w-full rounded-lg` | 1개 |
| 센서 그래프 영역 | `h-48 w-full rounded-lg` | 1개 |

```vue
<!-- BaseSkeleton.vue — 펄스 애니메이션 스켈레톤 -->
<template>
  <div
    class="animate-pulse bg-secondary-200 dark:bg-secondary-700 rounded"
    :class="[$attrs.class]"
  />
</template>
```

---

### 6.2 인증 토큰 만료 — 자동 갱신 및 만료 모달

```mermaid
flowchart TD
    API_CALL(["Axios API 호출"])
    API_CALL --> RESPONSE{"응답 코드?"}

    RESPONSE -- "2xx 성공" --> SUCCESS["정상 처리"]
    RESPONSE -- "401 TOKEN_EXPIRED" --> CHECK_RETRY{"_retry 플래그?"}

    CHECK_RETRY -- "false (첫 번째 시도)" --> SET_RETRY["original._retry = true"]
    SET_RETRY --> REFRESH_CALL["POST /auth/refresh\n(쿠키 자동 전송)"]

    REFRESH_CALL --> REFRESH_OK{"갱신 성공?"}
    REFRESH_OK -- "200 OK" --> FETCH_ME_CALL["GET /auth/me\ncurrentUser 복원"]
    FETCH_ME_CALL --> RETRY["원래 요청 재시도\nhttp(originalConfig)"]
    RETRY --> SUCCESS

    REFRESH_OK -- "401 (RefreshToken 만료)" --> LOGOUT_PROCESS["useAuthStore.logout()\nlocalStorage 초기화"]
    LOGOUT_PROCESS --> SHOW_MODAL["useUIStore.setTokenExpired(true)\n전역 TokenExpiredModal 표시"]

    SHOW_MODAL --> MODAL_DISPLAY["TokenExpiredModal 렌더링\n'로그인 세션이 만료되었습니다.\n보안을 위해 자동으로 로그아웃됩니다.'\n[다시 로그인] 버튼"]

    MODAL_DISPLAY --> CLICK_LOGIN["[다시 로그인] 버튼 클릭"]
    CLICK_LOGIN --> NAVIGATE["router.push('/login?reason=session_expired')"]
    NAVIGATE --> LOGIN_PAGE_MSG["로그인 페이지\n안내 배너: '세션이 만료되어 로그아웃되었습니다.'"]

    CHECK_RETRY -- "true (이미 재시도함)" --> SKIP_RETRY["갱신 루프 방지\n에러 그대로 반환"]
```

**TokenExpiredModal 컴포넌트**

```vue
<!-- src/components/global/TokenExpiredModal.vue -->
<template>
  <BaseModal
    :model-value="showTokenExpiredModal"
    title="세션 만료"
    size="sm"
    :close-on-backdrop="false"  <!-- 강제 모달 — 배경 클릭으로 닫기 불가 -->
  >
    <div class="flex flex-col items-center gap-4 py-2 text-center">
      <div class="w-14 h-14 rounded-full bg-warning-100 flex items-center justify-center">
        <LockClosedIcon class="w-7 h-7 text-warning-500" />
      </div>
      <p class="text-sm text-secondary-600 dark:text-secondary-300">
        로그인 세션이 만료되었습니다.<br />
        보안을 위해 자동으로 로그아웃 처리되었습니다.
      </p>
    </div>
    <template #footer>
      <BaseButton variant="solid-primary" size="md" class="w-full" @click="goToLogin">
        다시 로그인
      </BaseButton>
    </template>
  </BaseModal>
</template>

<script setup lang="ts">
import { storeToRefs } from "pinia"
import { useRouter } from "vue-router"
import { useUIStore } from "@/stores/ui"

const router  = useRouter()
const uiStore = useUIStore()
const { showTokenExpiredModal } = storeToRefs(uiStore)

function goToLogin() {
  uiStore.setTokenExpired(false)
  router.push("/login?reason=session_expired")
}
</script>
```

---

### 6.3 빈 결과 — Empty State 디자인

**원칙**: "아무것도 없음"은 오류가 아닙니다. 사용자가 다음 행동을 알 수 있도록 안내합니다.

```mermaid
flowchart LR
    API_RESULT(["API 응답\n200 OK"])
    API_RESULT --> LENGTH{"data.length?"}

    LENGTH -- "> 0" --> RENDER_LIST["목록 렌더링"]
    LENGTH -- "=== 0" --> CHECK_FILTER{"필터/검색\n조건 있음?"}

    CHECK_FILTER -- "있음" --> FILTERED_EMPTY["필터 Empty State\n아이콘: FunnelIcon\n타이틀: '검색 결과가 없습니다'\n설명: '다른 조건으로 검색해보세요'\n액션: [필터 초기화] 버튼"]

    CHECK_FILTER -- "없음" --> FULL_EMPTY["전체 Empty State\n아이콘: 도메인 아이콘\n타이틀: 도메인별 안내\n설명: 등록/생성 유도 문구\n액션: [등록 버튼] (권한 있는 경우)"]
```

**Empty State 도메인별 메시지 정의**

| 화면 | 아이콘 | 타이틀 | 설명 | 액션 버튼 |
|---|---|---|---|---|
| 차량 목록 (전체) | `TruckIcon` | 등록된 차량이 없습니다 | 새 차량을 등록하면 이곳에 표시됩니다 | [차량 등록] (ADMIN/MANAGER) |
| 차량 목록 (필터) | `FunnelIcon` | 검색 결과가 없습니다 | 선택한 상태에 해당하는 차량이 없습니다 | [필터 초기화] |
| 알림 목록 (전체) | `BellSlashIcon` | 알림이 없습니다 | 모든 차량이 정상 운행 중입니다 | — |
| 알림 목록 (미확인) | `CheckCircleIcon` | 미확인 알림이 없습니다 | 모든 알림을 확인했습니다 | — |
| 운행 기록 | `MapIcon` | 운행 기록이 없습니다 | 이 차량의 운행 기록이 없습니다 | — |
| 센서 데이터 | `ChartBarIcon` | 센서 데이터가 없습니다 | 선택한 기간에 데이터가 없습니다 | [기간 변경] |

```vue
<!-- BaseEmptyState.vue -->
<template>
  <div class="flex flex-col items-center justify-center gap-4 py-12 px-6 text-center">
    <!-- 아이콘 -->
    <div class="w-16 h-16 rounded-full bg-secondary-100 dark:bg-secondary-700
                flex items-center justify-center">
      <component :is="resolvedIcon" class="w-8 h-8 text-secondary-400 dark:text-secondary-500" />
    </div>

    <!-- 텍스트 -->
    <div class="flex flex-col gap-1">
      <h3 class="text-base font-semibold text-secondary-700 dark:text-secondary-300">
        {{ title }}
      </h3>
      <p class="text-sm text-secondary-400 dark:text-secondary-500 max-w-xs">
        {{ description }}
      </p>
    </div>

    <!-- 액션 버튼 (선택) -->
    <BaseButton
      v-if="actionLabel"
      variant="outline-primary"
      size="md"
      @click="$emit('action')"
    >
      {{ actionLabel }}
    </BaseButton>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue"
import * as HeroIcons from "@heroicons/vue/24/outline"

const props = defineProps<{
  icon:          string
  title:         string
  description:   string
  actionLabel?:  string
}>()

defineEmits<{ action: [] }>()

const resolvedIcon = computed(() => (HeroIcons as any)[props.icon] ?? HeroIcons.InboxIcon)
</script>
```

---

## 전역 Toast 시스템

```mermaid
flowchart LR
    TRIGGER(["Toast 발생 트리거\nAPI 에러 / 성공 / WebSocket 알림"])
    TRIGGER --> STORE["useUIStore.addToast({\n  type, message, duration\n})"]
    STORE --> QUEUE["toastQueue에 추가\nid = timestamp + random"]
    QUEUE --> RENDER["ToastContainer.vue\n화면 우상단 fixed 포지션"]
    RENDER --> ANIM["TransitionGroup 애니메이션\nenter: slide-in-right\nleave: fade-out"]
    ANIM --> DISPLAY["Toast 표시"]
    DISPLAY --> TIMER["duration 후 자동 제거\nsetTimeout → removeToast(id)"]
    DISPLAY --> CLOSE_BTN["X 버튼 클릭 → 즉시 제거"]

    TIMER --> REMOVE["toastQueue에서 제거"]
    CLOSE_BTN --> REMOVE
```

**Toast 타입별 규격**

| 타입 | 지속 시간 | 색상 | 사용 상황 |
|---|---|---|---|
| `success` | 3,000ms | 초록 | 저장 완료, 알림 확인 처리 |
| `info` | 3,000ms | 파란 | 일반 안내, 상태 변경 알림 |
| `warning` | 5,000ms | 노랑 | 배터리 부족, 주의 알림 |
| `error` | 7,000ms | 빨강 | API 오류, 과속 감지 |

```typescript
// src/composables/useToast.ts
import { useUIStore } from "@/stores/ui"

export function useToast() {
  const uiStore = useUIStore()
  return {
    success: (message: string) => uiStore.addToast({ type: "success", message, duration: 3000 }),
    info:    (message: string) => uiStore.addToast({ type: "info",    message, duration: 3000 }),
    warning: (message: string) => uiStore.addToast({ type: "warning", message, duration: 5000 }),
    error:   (message: string) => uiStore.addToast({ type: "error",   message, duration: 7000 }),
  }
}
```

---

## 전역 예외 처리 매트릭스

| 에러 코드 | HTTP | UX 처리 방식 | 위치 |
|---|---|---|---|
| `TOKEN_EXPIRED` | 401 | 자동 갱신 시도 → 실패 시 TokenExpiredModal | 전역 (Axios 인터셉터) |
| `TOKEN_INVALID` | 401 | 강제 로그아웃 → 로그인 페이지 | 전역 |
| `FORBIDDEN` | 403 | Toast 에러 + /403 페이지 이동 | 전역 |
| `VEHICLE_NOT_FOUND` | 404 | 안내 모달 + 목록으로 이동 | VehicleDetailView |
| `DUPLICATE_PLATE` | 409 | 폼 인라인 에러 메시지 | 차량 등록 폼 |
| `DUPLICATE_EMAIL` | 409 | 폼 인라인 에러 메시지 | 사용자 등록 폼 |
| `VEHICLE_HAS_DATA` | 422 | Toast 에러 + 상세 안내 텍스트 | 차량 삭제 확인 모달 |
| `DRIVER_ALREADY_ASSIGNED` | 422 | Toast 에러 | 배차 변경 폼 |
| `VALIDATION_ERROR` | 400 | 각 필드 하단 에러 메시지 | 모든 폼 |
| `INTERNAL_ERROR` | 500 | Toast 에러 '서버 오류, 잠시 후 재시도' | 전역 |
| 네트워크 오류 | — | Toast 에러 '네트워크 연결을 확인해주세요' | 전역 |

---

> **개정 이력**  
> - v1.0 (2026-04-13): 초안 작성 — Flow 5개, 예외 처리 가이드 3종, Toast 시스템, 전역 에러 매트릭스
