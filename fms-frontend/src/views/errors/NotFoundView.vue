<template>
  <div class="min-h-screen bg-background dark:bg-secondary-900 flex items-center justify-center px-4">
    <div class="text-center max-w-md">
      <p class="text-7xl font-black text-secondary-200 dark:text-secondary-700 mb-4">404</p>
      <h1 class="text-xl font-bold text-secondary-900 dark:text-white mb-2">페이지를 찾을 수 없습니다</h1>
      <p class="text-sm text-secondary-500 dark:text-secondary-400 mb-8">
        요청하신 페이지가 존재하지 않거나 이동되었습니다.
      </p>
      <RouterLink
        to="/app/dashboard"
        class="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary-500 hover:bg-primary-600
               text-white text-sm font-medium transition-colors"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
        </svg>
        대시보드로 이동
      </RouterLink>
    </div>
  </div>
</template>
