<template>
  <div class="min-h-screen bg-gray-50">
    <header class="bg-white border-b border-gray-200 shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center gap-8 h-16">
            <div class="flex items-center gap-3 h-16">
              <img src="/assets/mjauwser.webp" width="128" alt="Mjauwser Logo" class="h-16 w-auto" />
              <h1 class="text-xl font-bold text-gray-900">Mjauwser</h1>
            </div>
            <nav class="flex gap-4">
              <NuxtLink to="/admin" class="text-sm font-bold text-gray-600 hover:text-gray-900 px-4 py-1 rounded-full"
                :class="$route.path.startsWith('/admin') && !$route.path.startsWith('/admin/cats') && !$route.path.startsWith('/admin/judges') && !$route.path.startsWith('/admin/shows') ? 'bg-gray-900 text-white hover:text-white' : 'text-gray-600 hover:bg-gray-100'"
              >
                Översikt
              </NuxtLink>
              <NuxtLink to="/admin/shows" class="text-sm font-bold text-gray-600 hover:text-gray-900 px-4 py-1 rounded-full"
                :class="$route.path.startsWith('/admin/shows') ? 'bg-gray-900 text-white hover:text-white' : 'text-gray-600 hover:bg-gray-100'"
              >
                Utställningar
              </NuxtLink>
              <NuxtLink to="/admin/cats" class="text-sm font-bold text-gray-600 hover:text-gray-900 px-4 py-1 rounded-full"
                :class="$route.path.startsWith('/admin/cats') ? 'bg-gray-900 text-white hover:text-white' : 'text-gray-600 hover:bg-gray-100'"
              >
                Katter
              </NuxtLink>
            </nav>
          </div>
          <div class="text-xs text-gray-400">
            <slot name="status" />
          </div>
        </div>
      </div>
    </header>
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <slot />
    </main>
  </div>
</template>
