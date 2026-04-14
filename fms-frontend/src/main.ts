import { createApp } from "vue"
import { createPinia } from "pinia"

import "./style.css"
import App from "./App.vue"
import router from "./router"

// ── 다크 모드 초기화 ──────────────────────────────────────────
// TailwindCSS darkMode: "class" 전략 —
// localStorage의 "theme" 값이 "dark"이거나 OS 설정이 dark면 활성화
const savedTheme  = localStorage.getItem("theme")
const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches

if (savedTheme === "dark" || (!savedTheme && prefersDark)) {
  document.documentElement.classList.add("dark")
}

// ── 앱 생성 및 플러그인 등록 ──────────────────────────────────
const app = createApp(App)

app.use(createPinia())  // Pinia (Store가 router guard에서 사용되므로 router보다 먼저 등록)
app.use(router)

app.mount("#app")
