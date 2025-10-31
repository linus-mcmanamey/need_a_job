<script setup>
import { ref } from 'vue'
import { useUIStore } from '../stores/uiStore'

const uiStore = useUIStore()
const dropdownOpen = ref(false)
const searchQuery = ref('')

const handleSearch = () => {
  console.log('Searching for:', searchQuery.value)
  // Implement search functionality here
}
</script>

<template>
  <div class="sticky top-0 z-30 bg-slate-850/95 backdrop-blur-sm border-b border-slate-800/50">
    <div class="h-16 px-6 flex items-center justify-between">
      <!-- Left Section -->
      <div class="flex items-center gap-4">
        <!-- Mobile Hamburger -->
        <button
          class="lg:hidden p-2 rounded-lg hover:bg-slate-800 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500/50"
          @click="uiStore.toggleSidebar()"
        >
          <svg
            class="h-5 w-5 text-slate-400"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path d="M0 3h20v2H0V3zm0 6h20v2H0V9zm0 6h20v2H0v-2z" />
          </svg>
        </button>

        <!-- Search Bar -->
        <div class="relative">
          <input
            v-model="searchQuery"
            type="search"
            placeholder="Search jobs..."
            class="w-64 xl:w-96 h-9 pl-10 pr-4 rounded-lg border border-slate-700 bg-slate-800 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 transition-all duration-200"
            @keyup.enter="handleSearch"
          />
          <button
            class="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
            @click="handleSearch"
          >
            <svg
              class="h-4 w-4"
              fill="currentColor"
              viewBox="0 0 56.966 56.966"
            >
              <path
                d="M55.146,51.887L41.588,37.786c3.486-4.144,5.396-9.358,5.396-14.786c0-12.682-10.318-23-23-23s-23,10.318-23,23  s10.318,23,23,23c4.761,0,9.298-1.436,13.177-4.162l13.661,14.208c0.571,0.593,1.339,0.92,2.162,0.92  c0.779,0,1.518-0.297,2.079-0.837C56.255,54.982,56.293,53.08,55.146,51.887z M23.984,6c9.374,0,17,7.626,17,17s-7.626,17-17,17  s-17-7.626-17-17S14.61,6,23.984,6z"
              />
            </svg>
          </button>
        </div>
      </div>

      <!-- Right Section -->
      <div class="flex items-center gap-2">
        <!-- Notifications -->
        <button
          class="relative p-2 rounded-lg hover:bg-slate-800 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500/50"
        >
          <svg
            class="h-5 w-5 text-slate-400"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <path d="M0 0h24v24H0z" fill="none" />
            <path
              d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07-1.63-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.64 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2zm-2 1H8v-6c0-2.48 1.51-4.5 4-4.5s4 2.02 4 4.5v6z"
            />
          </svg>
          <!-- Notification Badge -->
          <span class="absolute top-1 right-1 w-2 h-2 bg-danger-500 rounded-full border border-slate-850"></span>
        </button>

        <!-- User Profile Dropdown -->
        <div class="relative">
          <button
            class="flex items-center gap-2 p-1.5 rounded-lg hover:bg-slate-800 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            @click="dropdownOpen = !dropdownOpen"
          >
            <div class="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-white text-sm font-semibold">
              JD
            </div>
            <svg
              class="h-4 w-4 text-slate-400 transition-transform duration-200"
              :class="{ 'rotate-180': dropdownOpen }"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fill-rule="evenodd"
                d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                clip-rule="evenodd"
              />
            </svg>
          </button>

          <!-- Dropdown Menu -->
          <transition
            enter-active-class="transition ease-out duration-100"
            enter-from-class="transform opacity-0 scale-95"
            enter-to-class="transform opacity-100 scale-100"
            leave-active-class="transition ease-in duration-75"
            leave-from-class="transform opacity-100 scale-100"
            leave-to-class="transform opacity-0 scale-95"
          >
            <div
              v-if="dropdownOpen"
              class="absolute right-0 mt-2 w-56 bg-slate-850 border border-slate-800/50 rounded-lg shadow-lg overflow-hidden"
            >
              <div class="px-4 py-3 border-b border-slate-800/50">
                <p class="text-sm font-semibold text-slate-100">John Doe</p>
                <p class="text-xs text-slate-400 mt-0.5">john.doe@example.com</p>
              </div>
              <a
                href="#"
                class="block px-4 py-2.5 text-sm font-medium text-slate-300 hover:bg-slate-800 hover:text-slate-100 transition-colors flex items-center gap-2"
              >
                <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fill-rule="evenodd"
                    d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                    clip-rule="evenodd"
                  />
                </svg>
                My Profile
              </a>
              <a
                href="#"
                class="block px-4 py-2.5 text-sm font-medium text-slate-300 hover:bg-slate-800 hover:text-slate-100 transition-colors flex items-center gap-2"
              >
                <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fill-rule="evenodd"
                    d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z"
                    clip-rule="evenodd"
                  />
                </svg>
                Settings
              </a>
              <div class="border-t border-slate-800/50"></div>
              <a
                href="#"
                class="block px-4 py-2.5 text-sm font-medium text-danger-400 hover:bg-danger-950/30 hover:text-danger-300 transition-colors flex items-center gap-2"
              >
                <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fill-rule="evenodd"
                    d="M3 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z"
                    clip-rule="evenodd"
                  />
                </svg>
                Logout
              </a>
            </div>
          </transition>
        </div>
      </div>
    </div>
  </div>
</template>
