export default defineNuxtConfig({
  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt',
    '@hypernym/nuxt-anime',
  ],
  tailwindcss: {
    config: {
      theme: {
        extend: {
          fontFamily: {
            sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
          },
          colors: {
            'almost-black': '#0a0a0a',
          },
        },
      },
      content: [
        './components/**/*.{vue,js,ts}',
        './layouts/**/*.vue',
        './pages/**/*.vue',
        './app.vue',
      ],
    },
  },
  vite: {
    server: {
      proxy: {
        '/api': { target: process.env.API_PROXY_TARGET || 'http://localhost:8000', changeOrigin: true },
      },
    },
  },
  runtimeConfig: {
    public: {
      wsBase: 'ws://localhost:8000',
    },
  },
  css: ['~/assets/css/main.css'],
  devtools: { enabled: true },
  compatibilityDate: '2024-09-01',
})
