<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useJobStore } from '../stores/jobStore'
import Sidebar from './Sidebar.vue'
import Navbar from './Navbar.vue'
import JobTable from './JobTable.vue'
import PipelineView from './PipelineView.vue'
import PendingJobs from './PendingJobs.vue'
import SearchConfig from './SearchConfig.vue'

// Get job store
const jobStore = useJobStore()

// Active tab
const activeTab = ref('jobs')

// Tab options
const tabs = [
  { id: 'jobs', label: 'Jobs', icon: '📋' },
  { id: 'pipeline', label: 'Pipeline', icon: '⚙️' },
  { id: 'pending', label: 'Pending', icon: '⏳' },
]

// Handle navigation from sidebar
const handleNavigate = (viewId) => {
  console.log('[Dashboard] Navigation to:', viewId)

  // Map sidebar navigation to tabs
  // 'dashboard' -> default to 'jobs'
  if (viewId === 'dashboard') {
    activeTab.value = 'jobs'
  } else if (['jobs', 'pipeline', 'pending', 'settings'].includes(viewId)) {
    activeTab.value = viewId
  }
}

// Handle discover jobs button click
const handleDiscoverJobs = async () => {
  console.log('[Dashboard] Discover jobs clicked')
  try {
    await jobStore.discoverJobs()
  } catch (err) {
    console.error('[Dashboard] Discovery failed:', err)
    // Error is already handled in store
  }
}

// Initialize store on mount
onMounted(async () => {
  console.log('[Dashboard] Component mounted, initializing store')
  await jobStore.initialize()
})

// Cleanup on unmount
onUnmounted(() => {
  console.log('[Dashboard] Component unmounting, cleaning up store')
  jobStore.cleanup()
})
</script>

<template>
  <div class="flex min-h-screen bg-slate-950">
    <!-- Sidebar -->
    <Sidebar :activeView="activeTab" @navigate="handleNavigate" />

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col lg:ml-64">
      <!-- Navbar -->
      <Navbar />

      <!-- Page Content -->
      <main class="flex-1 p-6">
        <!-- Header -->
        <div class="mb-8 animate-fade-in">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-4xl font-bold text-slate-50">
                Job Application Dashboard
              </h1>
              <p class="text-slate-400 mt-2 text-lg">Monitor and manage your automated job applications</p>
            </div>
            <!-- Right side actions -->
            <div class="flex items-center space-x-4">
              <!-- Discover Jobs Button -->
              <button
                @click="handleDiscoverJobs"
                :disabled="jobStore.loading.discovering"
                class="group relative flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-primary-500 to-accent-500 rounded-xl font-semibold text-slate-50 shadow-lg transition-all duration-300 hover:shadow-xl hover:shadow-primary-500/50 hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-slate-950 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 disabled:hover:shadow-lg overflow-hidden"
              >
                <!-- Animated gradient background on hover -->
                <span class="absolute inset-0 bg-gradient-to-r from-primary-600 to-accent-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></span>

                <!-- Content -->
                <span class="relative z-10 text-xl transition-transform duration-300" :class="jobStore.loading.discovering ? 'animate-spin' : ''">
                  {{ jobStore.loading.discovering ? '⏳' : '🔍' }}
                </span>
                <span class="relative z-10 whitespace-nowrap">
                  {{ jobStore.loading.discovering ? 'Discovering...' : 'Discover Jobs' }}
                </span>
              </button>

              <!-- Connection Status Indicator -->
              <div class="flex items-center space-x-2 px-5 py-2.5 rounded-full shadow-sm backdrop-blur-sm border" :class="{
                'bg-success-50/80 border-success-200': jobStore.connectionStatus === 'connected',
                'bg-warning-50/80 border-warning-200': jobStore.connectionStatus === 'connecting' || jobStore.connectionStatus === 'reconnecting',
                'bg-danger-50/80 border-danger-200': jobStore.connectionStatus === 'disconnected'
              }">
                <span class="h-2.5 w-2.5 rounded-full" :class="{
                  'bg-success-500 shadow-lg shadow-success-500/50': jobStore.connectionStatus === 'connected',
                  'bg-warning-500 animate-pulse shadow-lg shadow-warning-500/50': jobStore.connectionStatus === 'connecting' || jobStore.connectionStatus === 'reconnecting',
                  'bg-danger-500 shadow-lg shadow-danger-500/50': jobStore.connectionStatus === 'disconnected'
                }"></span>
                <span class="text-sm font-semibold" :class="{
                  'text-success-700': jobStore.connectionStatus === 'connected',
                  'text-warning-700': jobStore.connectionStatus === 'connecting' || jobStore.connectionStatus === 'reconnecting',
                  'text-danger-700': jobStore.connectionStatus === 'disconnected'
                }">
                  {{ jobStore.connectionStatus === 'connected' ? 'Connected' :
                     jobStore.connectionStatus === 'connecting' ? 'Connecting...' :
                     jobStore.connectionStatus === 'reconnecting' ? 'Reconnecting...' : 'Disconnected' }}
                </span>
              </div>
            </div>
          </div>
        </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8 animate-slide-up">
      <!-- Total Jobs -->
      <div class="group bg-slate-900 backdrop-blur-sm rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 p-6 border border-slate-800 hover:-translate-y-1 hover:border-slate-700">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-slate-400 text-sm font-semibold uppercase tracking-wider">Total Jobs</p>
            <p class="text-4xl font-bold text-slate-50 mt-2 group-hover:text-primary-400 transition-colors">
              {{ jobStore.jobStats.total }}
            </p>
          </div>
          <div class="bg-slate-800 rounded-2xl p-4 group-hover:bg-slate-700 transition-all duration-300">
            <span class="text-3xl">📊</span>
          </div>
        </div>
        <div class="mt-4 pt-4 border-t border-slate-800">
          <div class="flex items-center text-sm text-slate-400">
            <span class="inline-block w-2 h-2 bg-primary-500 rounded-full mr-2"></span>
            All tracked applications
          </div>
        </div>
      </div>

      <!-- Pending -->
      <div class="group bg-slate-900 backdrop-blur-sm rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 p-6 border border-slate-800 hover:-translate-y-1 hover:border-slate-700">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-slate-400 text-sm font-semibold uppercase tracking-wider">Pending</p>
            <p class="text-4xl font-bold text-warning-400 mt-2 group-hover:text-warning-300 transition-colors">
              {{ jobStore.jobStats.pending }}
            </p>
          </div>
          <div class="bg-slate-800 rounded-2xl p-4 group-hover:bg-slate-700 transition-all duration-300">
            <span class="text-3xl">⏳</span>
          </div>
        </div>
        <div class="mt-4 pt-4 border-t border-slate-800">
          <div class="flex items-center text-sm text-slate-400">
            <span class="inline-block w-2 h-2 bg-warning-500 rounded-full mr-2 animate-pulse"></span>
            Awaiting review
          </div>
        </div>
      </div>

      <!-- Applied -->
      <div class="group bg-slate-900 backdrop-blur-sm rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 p-6 border border-slate-800 hover:-translate-y-1 hover:border-slate-700">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-slate-400 text-sm font-semibold uppercase tracking-wider">Applied</p>
            <p class="text-4xl font-bold text-success-400 mt-2 group-hover:text-success-300 transition-colors">
              {{ jobStore.jobStats.applied }}
            </p>
          </div>
          <div class="bg-slate-800 rounded-2xl p-4 group-hover:bg-slate-700 transition-all duration-300">
            <span class="text-3xl">✅</span>
          </div>
        </div>
        <div class="mt-4 pt-4 border-t border-slate-800">
          <div class="flex items-center text-sm text-slate-400">
            <span class="inline-block w-2 h-2 bg-success-500 rounded-full mr-2"></span>
            Successfully submitted
          </div>
        </div>
      </div>

      <!-- Rejected -->
      <div class="group bg-slate-900 backdrop-blur-sm rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 p-6 border border-slate-800 hover:-translate-y-1 hover:border-slate-700">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-slate-400 text-sm font-semibold uppercase tracking-wider">Rejected</p>
            <p class="text-4xl font-bold text-danger-400 mt-2 group-hover:text-danger-300 transition-colors">
              {{ jobStore.jobStats.rejected }}
            </p>
          </div>
          <div class="bg-slate-800 rounded-2xl p-4 group-hover:bg-slate-700 transition-all duration-300">
            <span class="text-3xl">❌</span>
          </div>
        </div>
        <div class="mt-4 pt-4 border-t border-slate-800">
          <div class="flex items-center text-sm text-slate-400">
            <span class="inline-block w-2 h-2 bg-danger-500 rounded-full mr-2"></span>
            Not proceeded
          </div>
        </div>
      </div>
    </div>

    <!-- Tab Navigation (only show for non-settings views) -->
    <div v-if="activeTab !== 'settings'" class="bg-slate-900 backdrop-blur-sm rounded-2xl shadow-lg border border-slate-800 mb-8 overflow-hidden">
      <div class="border-b border-slate-800 bg-slate-900">
        <nav class="flex -mb-px">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'relative py-4 px-8 font-semibold text-sm focus:outline-none focus:ring-2 focus:ring-slate-600 transition-all duration-300',
              activeTab === tab.id
                ? 'text-slate-50 bg-slate-800'
                : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/50'
            ]"
          >
            <span class="mr-2 text-lg">{{ tab.icon }}</span>
            {{ tab.label }}
            <span
              v-if="activeTab === tab.id"
              class="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-primary-500 to-accent-500"
            ></span>
          </button>
        </nav>
      </div>

      <!-- Tab Content -->
      <div class="p-8 bg-slate-900">
        <!-- Jobs Tab -->
        <div v-if="activeTab === 'jobs'" class="animate-fade-in">
          <JobTable />
        </div>

        <!-- Pipeline Tab -->
        <div v-if="activeTab === 'pipeline'" class="animate-fade-in">
          <PipelineView />
        </div>

        <!-- Pending Tab -->
        <div v-if="activeTab === 'pending'" class="animate-fade-in">
          <PendingJobs />
        </div>
      </div>
    </div>

    <!-- Search Configuration View -->
    <div v-if="activeTab === 'settings'" class="animate-fade-in">
      <SearchConfig />
    </div>

    <!-- Error Display -->
    <div v-if="jobStore.error" class="bg-danger-900/20 border-l-4 border-danger-500 rounded-xl p-5 shadow-lg animate-slide-up backdrop-blur-sm border border-danger-800">
      <div class="flex items-start">
        <span class="text-danger-400 mr-3 text-2xl">⚠️</span>
        <div class="flex-1">
          <p class="text-danger-300 font-bold text-lg">Error</p>
          <p class="text-danger-400 text-sm mt-1.5">{{ jobStore.error }}</p>
        </div>
        <button
          @click="jobStore.error = null"
          class="text-danger-400 hover:text-danger-300 transition-colors ml-4 focus:outline-none focus:ring-2 focus:ring-danger-500"
        >
          <span class="text-xl">×</span>
        </button>
      </div>
    </div>

    <!-- Discovery Notification -->
    <div
      v-if="jobStore.discoveryNotification"
      class="rounded-xl p-5 shadow-lg animate-slide-up backdrop-blur-sm border mt-6 transition-all duration-300"
      :class="{
        'bg-success-900/20 border-l-4 border-success-500 border-success-800': jobStore.discoveryNotification.type === 'success',
        'bg-danger-900/20 border-l-4 border-danger-500 border-danger-800': jobStore.discoveryNotification.type === 'error'
      }"
    >
      <div class="flex items-start">
        <span class="mr-3 text-2xl" :class="{
          'text-success-400': jobStore.discoveryNotification.type === 'success',
          'text-danger-400': jobStore.discoveryNotification.type === 'error'
        }">
          {{ jobStore.discoveryNotification.type === 'success' ? '✅' : '❌' }}
        </span>
        <div class="flex-1">
          <p class="font-bold text-lg" :class="{
            'text-success-300': jobStore.discoveryNotification.type === 'success',
            'text-danger-300': jobStore.discoveryNotification.type === 'error'
          }">
            {{ jobStore.discoveryNotification.type === 'success' ? 'Success' : 'Error' }}
          </p>
          <p class="text-sm mt-1.5" :class="{
            'text-success-400': jobStore.discoveryNotification.type === 'success',
            'text-danger-400': jobStore.discoveryNotification.type === 'error'
          }">
            {{ jobStore.discoveryNotification.message }}
          </p>
        </div>
        <button
          @click="jobStore.discoveryNotification = null"
          class="transition-colors ml-4 focus:outline-none focus:ring-2"
          :class="{
            'text-success-400 hover:text-success-300 focus:ring-success-500': jobStore.discoveryNotification.type === 'success',
            'text-danger-400 hover:text-danger-300 focus:ring-danger-500': jobStore.discoveryNotification.type === 'error'
          }"
        >
          <span class="text-xl">×</span>
        </button>
      </div>
    </div>
      </main>
    </div>
  </div>
</template>
