<template>
  <div class="min-h-screen bg-background dark:bg-secondary-900 flex items-center justify-center px-4">
    <div class="text-center max-w-md">
      <p class="text-7xl font-black text-secondary-200 dark:text-secondary-700 mb-4">403</p>
      <h1 class="text-xl font-bold text-secondary-900 dark:text-white mb-2">접근 권한이 없습니다</h1>
      <p class="text-sm text-secondary-500 dark:text-secondary-400 mb-8">
        이 페이지를 볼 수 있는 권한이 없습니다.<br>관리자에게 문의하세요.
      </p>
      <div class="flex items-center justify-center gap-3">
        <button
          @click="$router.back()"
          class="px-4 py-2 rounded-lg border border-secondary-300 dark:border-secondary-600
                 text-sm font-medium text-secondary-700 dark:text-secondary-300
                 hover:bg-secondary-50 dark:hover:bg-secondary-800 transition-colors"
        >
          이전으로
        </button>
        <RouterLink
          to="/app/dashboard"
          class="px-4 py-2 rounded-lg bg-primary-500 hover:bg-primary-600 text-white
                 text-sm font-medium transition-colors"
        >
          대시보드로
        </RouterLink>
      </div>
    </div>
  </div>
</template>
