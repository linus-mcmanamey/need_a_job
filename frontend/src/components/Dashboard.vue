<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useJobStore } from '../stores/jobStore'
import { Icon } from '@iconify/vue'
import Sidebar from './Sidebar.vue'
import Navbar from './Navbar.vue'
import JobTable from './JobTable.vue'
import PipelineView from './PipelineView.vue'
import PendingJobs from './PendingJobs.vue'
import SearchConfig from './SearchConfig.vue'
import ApplicationHistory from './ApplicationHistory.vue'

// Get job store
const jobStore = useJobStore()

// Active tab
const activeTab = ref('jobs')

// Tab options
const tabs = [
  { id: 'jobs', label: 'Jobs', icon: 'heroicons:clipboard-document-list' },
  { id: 'pipeline', label: 'Pipeline', icon: 'heroicons:cog-6-tooth' },
  { id: 'pending', label: 'Pending', icon: 'heroicons:clock' },
  { id: 'history', label: 'History', icon: 'heroicons:clock' },
]

// Handle navigation from sidebar
const handleNavigate = (viewId) => {
  console.log('[Dashboard] Navigation to:', viewId)

  // Map sidebar navigation to tabs
  // 'dashboard' -> default to 'jobs'
  if (viewId === 'dashboard') {
    activeTab.value = 'jobs'
  } else if (['jobs', 'pipeline', 'pending', 'history', 'settings'].includes(viewId)) {
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
  <div class="flex min-h-screen bg-slate-925">
    <!-- Sidebar -->
    <Sidebar :activeView="activeTab" @navigate="handleNavigate" />

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col lg:ml-64">
      <!-- Navbar -->
      <Navbar />

      <!-- Page Content -->
      <main class="flex-1 p-8">
        <!-- Header -->
        <div class="mb-6 animate-fade-in">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-3xl font-bold text-slate-50 tracking-tight">
                Job Application Dashboard
              </h1>
              <p class="text-slate-400 mt-2 text-sm">Monitor and manage your automated job applications</p>
            </div>
            <!-- Right side actions -->
            <div class="flex items-center space-x-4">
              <!-- Discover Jobs Button -->
              <button
                @click="handleDiscoverJobs"
                :disabled="jobStore.loading.discovering"
                class="flex items-center space-x-2 px-4 py-2.5 bg-primary-600 rounded-lg font-semibold text-sm text-white shadow-sm transition-all duration-200 hover:bg-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-slate-925 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Icon
                  :icon="jobStore.loading.discovering ? 'heroicons:clock' : 'heroicons:magnifying-glass'"
                  class="w-5 h-5"
                  :class="jobStore.loading.discovering ? 'animate-spin' : ''"
                />
                <span>{{ jobStore.loading.discovering ? 'Discovering...' : 'Discover Jobs' }}</span>
              </button>

              <!-- Connection Status Indicator -->
              <div class="flex items-center space-x-2 px-3 py-2 rounded-lg border" :class="{
                'bg-success-950/30 border-success-800/50': jobStore.connectionStatus === 'connected',
                'bg-warning-950/30 border-warning-800/50': jobStore.connectionStatus === 'connecting' || jobStore.connectionStatus === 'reconnecting',
                'bg-danger-950/30 border-danger-800/50': jobStore.connectionStatus === 'disconnected'
              }">
                <span class="h-2 w-2 rounded-full" :class="{
                  'bg-success-500': jobStore.connectionStatus === 'connected',
                  'bg-warning-500 animate-pulse': jobStore.connectionStatus === 'connecting' || jobStore.connectionStatus === 'reconnecting',
                  'bg-danger-500': jobStore.connectionStatus === 'disconnected'
                }"></span>
                <span class="text-xs font-medium" :class="{
                  'text-success-400': jobStore.connectionStatus === 'connected',
                  'text-warning-400': jobStore.connectionStatus === 'connecting' || jobStore.connectionStatus === 'reconnecting',
                  'text-danger-400': jobStore.connectionStatus === 'disconnected'
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
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6 animate-slide-up">
      <!-- Total Jobs -->
      <div class="bg-slate-850 rounded-lg shadow-sm border border-slate-800/50 p-5 hover:border-slate-700 transition-all duration-200">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <p class="text-slate-400 text-xs font-medium uppercase tracking-wide mb-2">Total Jobs</p>
            <p class="text-3xl font-bold text-slate-50 tabular-nums">
              {{ jobStore.jobStats.total }}
            </p>
            <p class="text-xs text-slate-500 mt-2">All tracked applications</p>
          </div>
          <div class="bg-slate-800/50 rounded-lg p-2.5">
            <Icon icon="heroicons:chart-bar" class="w-8 h-8 text-slate-400" />
          </div>
        </div>
      </div>

      <!-- Pending -->
      <div class="bg-slate-850 rounded-lg shadow-sm border border-slate-800/50 p-5 hover:border-slate-700 transition-all duration-200">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <p class="text-slate-400 text-xs font-medium uppercase tracking-wide mb-2">Pending</p>
            <p class="text-3xl font-bold text-warning-400 tabular-nums">
              {{ jobStore.jobStats.pending }}
            </p>
            <p class="text-xs text-slate-500 mt-2">Awaiting review</p>
          </div>
          <div class="bg-slate-800/50 rounded-lg p-2.5">
            <Icon icon="heroicons:clock" class="w-8 h-8 text-warning-400" />
          </div>
        </div>
      </div>

      <!-- Applied -->
      <div class="bg-slate-850 rounded-lg shadow-sm border border-slate-800/50 p-5 hover:border-slate-700 transition-all duration-200">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <p class="text-slate-400 text-xs font-medium uppercase tracking-wide mb-2">Applied</p>
            <p class="text-3xl font-bold text-success-400 tabular-nums">
              {{ jobStore.jobStats.applied }}
            </p>
            <p class="text-xs text-slate-500 mt-2">Successfully submitted</p>
          </div>
          <div class="bg-slate-800/50 rounded-lg p-2.5">
            <Icon icon="heroicons:check-circle" class="w-8 h-8 text-success-400" />
          </div>
        </div>
      </div>

      <!-- Rejected -->
      <div class="bg-slate-850 rounded-lg shadow-sm border border-slate-800/50 p-5 hover:border-slate-700 transition-all duration-200">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <p class="text-slate-400 text-xs font-medium uppercase tracking-wide mb-2">Rejected</p>
            <p class="text-3xl font-bold text-danger-400 tabular-nums">
              {{ jobStore.jobStats.rejected }}
            </p>
            <p class="text-xs text-slate-500 mt-2">Not proceeded</p>
          </div>
          <div class="bg-slate-800/50 rounded-lg p-2.5">
            <Icon icon="heroicons:x-circle" class="w-8 h-8 text-danger-400" />
          </div>
        </div>
      </div>
    </div>

    <!-- Tab Navigation (only show for non-settings views) -->
    <div v-if="activeTab !== 'settings'" class="bg-slate-850 rounded-lg shadow-sm border border-slate-800/50 overflow-hidden">
      <div class="border-b border-slate-800/50">
        <nav class="flex">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'relative py-3 px-6 font-medium text-sm focus:outline-none transition-all duration-200 flex items-center',
              activeTab === tab.id
                ? 'text-slate-50 border-b-2 border-primary-500'
                : 'text-slate-400 hover:text-slate-200'
            ]"
          >
            <Icon :icon="tab.icon" class="w-4 h-4 mr-2" />
            {{ tab.label }}
          </button>
        </nav>
      </div>

      <!-- Tab Content -->
      <div class="p-6">
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

        <!-- History Tab -->
        <div v-if="activeTab === 'history'" class="animate-fade-in">
          <ApplicationHistory />
        </div>
      </div>
    </div>

    <!-- Search Configuration View -->
    <div v-if="activeTab === 'settings'" class="animate-fade-in">
      <SearchConfig />
    </div>

    <!-- Error Display -->
    <div v-if="jobStore.error" class="bg-danger-950/30 border-l-4 border-danger-500 rounded-lg p-4 shadow-sm animate-slide-up border border-danger-800/50">
      <div class="flex items-start">
        <Icon icon="heroicons:exclamation-triangle" class="w-5 h-5 text-danger-400 mr-3 flex-shrink-0" />
        <div class="flex-1">
          <p class="text-danger-300 font-semibold text-sm mb-1">Error</p>
          <p class="text-danger-200 text-sm">{{ jobStore.error }}</p>
        </div>
        <button
          @click="jobStore.error = null"
          class="text-danger-300 hover:text-danger-200 transition-colors ml-4 focus:outline-none focus:ring-2 focus:ring-danger-400 rounded p-0.5"
        >
          <Icon icon="heroicons:x-mark" class="w-5 h-5" />
        </button>
      </div>
    </div>

    <!-- Discovery Notification -->
    <div
      v-if="jobStore.discoveryNotification"
      class="rounded-lg p-4 shadow-sm animate-slide-up border mt-4 transition-all duration-300"
      :class="{
        'bg-success-950/30 border-l-4 border-success-500 border-success-800/50': jobStore.discoveryNotification.type === 'success',
        'bg-danger-950/30 border-l-4 border-danger-500 border-danger-800/50': jobStore.discoveryNotification.type === 'error'
      }"
    >
      <div class="flex items-start">
        <Icon
          :icon="jobStore.discoveryNotification.type === 'success' ? 'heroicons:check-circle' : 'heroicons:x-circle'"
          class="w-5 h-5 mr-3 flex-shrink-0"
          :class="{
            'text-success-400': jobStore.discoveryNotification.type === 'success',
            'text-danger-400': jobStore.discoveryNotification.type === 'error'
          }"
        />
        <div class="flex-1">
          <p class="font-semibold text-sm mb-1" :class="{
            'text-success-300': jobStore.discoveryNotification.type === 'success',
            'text-danger-300': jobStore.discoveryNotification.type === 'error'
          }">
            {{ jobStore.discoveryNotification.type === 'success' ? 'Success' : 'Error' }}
          </p>
          <p class="text-sm" :class="{
            'text-success-200': jobStore.discoveryNotification.type === 'success',
            'text-danger-200': jobStore.discoveryNotification.type === 'error'
          }">
            {{ jobStore.discoveryNotification.message }}
          </p>
        </div>
        <button
          @click="jobStore.discoveryNotification = null"
          class="transition-colors ml-4 focus:outline-none focus:ring-2 rounded p-0.5"
          :class="{
            'text-success-300 hover:text-success-200 focus:ring-success-400': jobStore.discoveryNotification.type === 'success',
            'text-danger-300 hover:text-danger-200 focus:ring-danger-400': jobStore.discoveryNotification.type === 'error'
          }"
        >
          <Icon icon="heroicons:x-mark" class="w-5 h-5" />
        </button>
      </div>
    </div>
      </main>
    </div>
  </div>
</template>
