<template>
  <div class="min-h-screen bg-background dark:bg-secondary-900 flex items-center justify-center px-4">
    <div class="w-full max-w-md">

      <!-- 로고 -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-primary-500 mb-4 shadow-lg">
          <svg class="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <h1 class="text-2xl font-bold text-secondary-900 dark:text-white">BikeFMS</h1>
        <p class="mt-1 text-sm text-secondary-500 dark:text-secondary-400">오토바이 통합 관제 시스템</p>
      </div>

      <!-- 로그인 카드 -->
      <div class="bg-surface dark:bg-secondary-800 rounded-2xl shadow-xl border border-secondary-200 dark:border-secondary-700 p-8">
        <h2 class="text-lg font-semibold text-secondary-900 dark:text-white mb-6">로그인</h2>

        <!-- 빠른 로그인 (테스트용) -->
        <div class="mb-6 pb-6 border-b border-slate-100 dark:border-secondary-700">
          <p class="text-xs font-semibold text-secondary-500 mb-3 uppercase tracking-wider">테스트 계정 자동 로그인</p>
          <div class="grid grid-cols-2 gap-3">
            <button
              type="button"
              @click="handleQuickLogin('admin@fms.io', 'admin123')"
              class="flex flex-col items-center justify-center p-3 rounded-xl border border-primary-100 dark:border-primary-900 bg-primary-50 dark:bg-primary-900/20 hover:bg-primary-100 dark:hover:bg-primary-900/40 transition-colors"
            >
              <span class="text-sm font-bold text-primary-700 dark:text-primary-300">관리자 (Admin)</span>
              <span class="text-xs text-primary-500 dark:text-primary-400 mt-0.5">전체 권한</span>
            </button>
            <button
              type="button"
              @click="handleQuickLogin('driver@fms.io', 'driver123')"
              class="flex flex-col items-center justify-center p-3 rounded-xl border border-secondary-200 dark:border-secondary-700 bg-secondary-50 dark:bg-secondary-800/50 hover:bg-secondary-100 dark:hover:bg-secondary-700 transition-colors"
            >
              <span class="text-sm font-bold text-secondary-700 dark:text-secondary-300">사용자 (Driver)</span>
              <span class="text-xs text-secondary-500 dark:text-secondary-400 mt-0.5">운행 내역 조회</span>
            </button>
          </div>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-5">

          <!-- 이메일 -->
          <div>
            <label class="block text-sm font-medium text-secondary-700 dark:text-secondary-300 mb-1.5">
              이메일
            </label>
            <div class="relative">
              <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg class="w-4 h-4 text-secondary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207"/>
                </svg>
              </span>
              <input
                v-model="form.email"
                type="email"
                placeholder="admin@example.com"
                autocomplete="email"
                required
                :class="[
                  'w-full pl-10 pr-4 py-2.5 rounded-lg border text-sm transition-colors',
                  'bg-white dark:bg-secondary-900 text-secondary-900 dark:text-white',
                  'placeholder:text-secondary-400',
                  error
                    ? 'border-danger-400 focus:ring-danger-300 focus:border-danger-400'
                    : 'border-secondary-300 dark:border-secondary-600 focus:border-primary-500 dark:focus:border-primary-400',
                  'focus:outline-none focus:ring-2 focus:ring-primary-200 dark:focus:ring-primary-800',
                ]"
              />
            </div>
          </div>

          <!-- 비밀번호 -->
          <div>
            <label class="block text-sm font-medium text-secondary-700 dark:text-secondary-300 mb-1.5">
              비밀번호
            </label>
            <div class="relative">
              <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg class="w-4 h-4 text-secondary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                </svg>
              </span>
              <input
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="비밀번호 입력"
                autocomplete="current-password"
                required
                :class="[
                  'w-full pl-10 pr-10 py-2.5 rounded-lg border text-sm transition-colors',
                  'bg-white dark:bg-secondary-900 text-secondary-900 dark:text-white',
                  'placeholder:text-secondary-400',
                  error
                    ? 'border-danger-400 focus:ring-danger-300'
                    : 'border-secondary-300 dark:border-secondary-600 focus:border-primary-500 dark:focus:border-primary-400',
                  'focus:outline-none focus:ring-2 focus:ring-primary-200 dark:focus:ring-primary-800',
                ]"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute inset-y-0 right-0 pr-3 flex items-center text-secondary-400 hover:text-secondary-600"
              >
                <svg v-if="showPassword" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
                </svg>
                <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- 에러 메시지 -->
          <Transition name="fade">
            <div
              v-if="error"
              class="flex items-center gap-2 px-3 py-2.5 rounded-lg
                     bg-danger-50 dark:bg-danger-900/30 border border-danger-200 dark:border-danger-700"
            >
              <svg class="w-4 h-4 text-danger-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              <p class="text-sm text-danger-700 dark:text-danger-300">{{ error }}</p>
            </div>
          </Transition>

          <!-- 로그인 버튼 -->
          <button
            type="submit"
            :disabled="authStore.isLoading"
            class="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg font-medium text-sm
                   bg-primary-500 hover:bg-primary-600 active:bg-primary-700 text-white
                   disabled:opacity-60 disabled:cursor-not-allowed
                   transition-colors focus:outline-none focus:ring-2 focus:ring-primary-300"
          >
            <svg v-if="authStore.isLoading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            {{ authStore.isLoading ? '로그인 중...' : '로그인' }}
          </button>

        </form>
      </div>

      <p class="mt-6 text-center text-xs text-secondary-400">© 2025 BikeFMS. All rights reserved.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue"
import { useRouter, useRoute } from "vue-router"
import { useAuthStore } from "@/stores/auth"

const router    = useRouter()
const route     = useRoute()
const authStore = useAuthStore()

const form         = ref({ email: "", password: "" })
const showPassword = ref(false)
const error        = ref("")

async function handleSubmit() {
  error.value = ""
  try {
    await authStore.login(form.value.email, form.value.password)
    const redirect = (route.query.redirect as string) || "/app/dashboard"
    router.push(redirect)
  } catch (e: unknown) {
    const err = e as { error?: { message?: string } }
    error.value = err?.error?.message ?? "이메일 또는 비밀번호를 확인해 주세요."
  }
}

async function handleQuickLogin(emailStr: string, passwordStr: string) {
  form.value.email = emailStr
  form.value.password = passwordStr
  await handleSubmit()
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
