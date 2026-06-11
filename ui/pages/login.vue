<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8 w-full max-w-sm">
      <h1 class="text-xl font-bold text-gray-900 mb-6 text-center">Logga in</h1>
      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Användarnamn</label>
          <input v-model="username" type="text" required autocomplete="username"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Lösenord</label>
          <input v-model="password" type="password" required autocomplete="current-password"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
        </div>
        <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
        <Btn type="submit" variant="primary" :disabled="loading" class="w-full justify-center">
          {{ loading ? 'Loggar in...' : 'Logga in' }}
        </Btn>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const router = useRouter()

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value, password: password.value }),
    })
    if (!res.ok) {
      const text = await res.text().catch(() => '')
      throw new Error(text || 'Inloggning misslyckades')
    }
    const data = await res.json()
    localStorage.setItem('auth_token', data.token)
    router.push('/admin')
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>
