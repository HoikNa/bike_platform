import type { Config } from "tailwindcss"

export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,ts,tsx}",
  ],

  // 다크 모드: class 전략 — main.ts에서 document.documentElement.classList.add("dark") 로 활성화
  darkMode: "class",

  theme: {
    extend: {
      // ── 폰트 ───────────────────────────────────────────────
      fontFamily: {
        sans: ["Noto Sans KR", "Pretendard", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },

      // ── 컬러 팔레트 ────────────────────────────────────────
      colors: {
        // Primary (브랜드 메인 — 딥블루)
        primary: {
          50:  "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",   // 기본 (bg-primary-500)
          600: "#2563eb",   // hover
          700: "#1d4ed8",   // active / pressed
          800: "#1e40af",
          900: "#1e3a8a",
          950: "#172554",
        },

        // Secondary (슬레이트 — 텍스트, 배경, 구분선)
        secondary: {
          50:  "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          300: "#cbd5e1",
          400: "#94a3b8",
          500: "#64748b",   // 기본
          600: "#475569",
          700: "#334155",
          800: "#1e293b",
          900: "#0f172a",
          950: "#020617",
        },

        // Background / Surface
        background: {
          DEFAULT: "#f1f5f9",
          subtle:  "#e2e8f0",
        },
        surface: {
          DEFAULT: "#ffffff",
          raised:  "#f8fafc",
          overlay: "#ffffff",
        },

        // Semantic — Success (정상/완료)
        success: {
          50:  "#f0fdf4",
          100: "#dcfce7",
          200: "#bbf7d0",
          400: "#4ade80",
          500: "#22c55e",   // 기본
          600: "#16a34a",
          700: "#15803d",
          900: "#14532d",
        },

        // Semantic — Warning (주의/배터리 부족)
        warning: {
          50:  "#fffbeb",
          100: "#fef3c7",
          200: "#fde68a",
          400: "#fbbf24",
          500: "#f59e0b",   // 기본
          600: "#d97706",
          700: "#b45309",
          900: "#78350f",
        },

        // Semantic — Danger (과속/사고/에러)
        danger: {
          50:  "#fff1f2",
          100: "#ffe4e6",
          200: "#fecdd3",
          400: "#fb7185",
          500: "#ef4444",   // 기본
          600: "#dc2626",
          700: "#b91c1c",
          900: "#7f1d1d",
        },

        // Semantic — Info (일반 알림)
        info: {
          50:  "#f0f9ff",
          100: "#e0f2fe",
          200: "#bae6fd",
          400: "#38bdf8",
          500: "#0ea5e9",   // 기본
          600: "#0284c7",
          700: "#0369a1",
          900: "#0c4a6e",
        },
      },

      // ── 커스텀 애니메이션 ──────────────────────────────────
      animation: {
        "fade-in":     "fadeIn 0.2s ease-out",
        "slide-up":    "slideUp 0.3s ease-out",
        "slide-in-right": "slideInRight 0.3s ease-out",
        "pulse-slow":  "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        fadeIn: {
          "0%":   { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%":   { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideInRight: {
          "0%":   { opacity: "0", transform: "translateX(16px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
      },
    },
  },

  plugins: [
    // @tailwindcss/line-clamp 은 v3.3+ 에서 core에 포함됨 — 별도 설치 불필요
  ],
} satisfies Config
