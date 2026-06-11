export default defineNuxtRouteMiddleware((to) => {
  if (!import.meta.client) return

  const token = localStorage.getItem('auth_token')
  if (!token) {
    return navigateTo('/login')
  }
})
