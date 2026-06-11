const TOKEN_KEY = 'auth_token'

export function useAuth() {
  function getToken(): string | null {
    if (!import.meta.client) return null
    return localStorage.getItem(TOKEN_KEY)
  }

  function setToken(token: string) {
    localStorage.setItem(TOKEN_KEY, token)
  }

  function clearToken() {
    localStorage.removeItem(TOKEN_KEY)
  }

  function isAuthenticated(): boolean {
    return !!getToken()
  }

  return { getToken, setToken, clearToken, isAuthenticated }
}
