<script setup>
import { useJobStore } from '../stores/jobStore'
import { Icon } from '@iconify/vue'
import { computed } from 'vue'

// Get job store
const jobStore = useJobStore()

// Pipeline metrics
const metrics = computed(() => {
  const counts = jobStore.pipeline.stage_counts || {}
  return [
    {
      label: 'Discovery Queue',
      count: counts.discovered || 0,
      color: 'bg-gradient-to-br from-blue-900/40 to-blue-800/20',
      textColor: 'text-blue-100',
      borderColor: 'border-blue-800',
      labelColor: 'text-blue-300',
      icon: 'heroicons:magnifying-glass',
    },
    {
      label: 'Active Processing',
      count: Object.values(counts).reduce((sum, val) => {
        return sum + (typeof val === 'number' ? val : 0)
      }, 0) - (counts.completed || 0) - (counts.rejected || 0),
      color: 'bg-gradient-to-br from-purple-900/40 to-purple-800/20',
      textColor: 'text-purple-100',
      borderColor: 'border-purple-800',
      labelColor: 'text-purple-300',
      icon: 'heroicons:cog-6-tooth',
    },
    {
      label: 'Completed',
      count: counts.completed || 0,
      color: 'bg-gradient-to-br from-green-900/40 to-green-800/20',
      textColor: 'text-green-100',
      borderColor: 'border-green-800',
      labelColor: 'text-green-300',
      icon: 'heroicons:check-circle',
    },
  ]
})

// Active jobs in pipeline
const activeJobs = computed(() => {
  return jobStore.pipeline.active_jobs || []
})

/**
 * Format timestamp
 */
function formatTime(timestamp) {
  if (!timestamp) return 'Unknown'

  try {
    const date = new Date(timestamp)
    return date.toLocaleTimeString()
  } catch {
    return 'Invalid'
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-3xl font-bold text-slate-50">Pipeline Overview</h2>
        <p class="text-slate-400 mt-1">
          Track your job application processing pipeline
        </p>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="jobStore.loading.pipeline" class="text-center py-16">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-3 border-primary-600 border-t-3"></div>
      <p class="text-slate-400 mt-4 font-medium">Loading pipeline metrics...</p>
    </div>

    <!-- Pipeline Content -->
    <div v-else class="space-y-6">
      <!-- Metrics Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div
          v-for="metric in metrics"
          :key="metric.label"
          :class="['rounded-xl border p-6 transition-all duration-200 hover:scale-105', metric.color, metric.borderColor]"
        >
          <div class="flex items-center justify-between mb-2">
            <span :class="['text-sm font-medium', metric.labelColor]">{{ metric.label }}</span>
            <Icon :icon="metric.icon" :class="['w-8 h-8', metric.textColor]" />
          </div>
          <p :class="['text-4xl font-bold', metric.textColor]">
            {{ metric.count }}
          </p>
        </div>
      </div>

      <!-- Active Jobs Section -->
      <div class="bg-slate-900/50 rounded-xl border border-slate-800 p-6">
        <h3 class="text-xl font-bold text-slate-100 mb-4 flex items-center">
          <Icon icon="heroicons:chart-bar" class="w-6 h-6 mr-2" />
          Active Jobs in Pipeline
        </h3>

        <!-- Empty State -->
        <div v-if="activeJobs.length === 0" class="text-center py-12 bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl border-2 border-dashed border-slate-700">
          <Icon icon="heroicons:arrow-trending-up" class="w-24 h-24 text-slate-600 mx-auto mb-4" />
          <h4 class="text-lg font-bold text-slate-200 mb-2">No Active Jobs</h4>
          <p class="text-slate-400">No jobs currently being processed in the pipeline</p>
        </div>

        <!-- Active Jobs Table -->
        <div v-else class="overflow-hidden rounded-xl border border-slate-800">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-slate-800">
              <thead class="bg-gradient-to-r from-slate-900 to-slate-800">
                <tr>
                  <th class="px-6 py-4 text-left text-xs font-bold text-slate-300 uppercase tracking-wider">
                    Job
                  </th>
                  <th class="px-6 py-4 text-left text-xs font-bold text-slate-300 uppercase tracking-wider">
                    Company
                  </th>
                  <th class="px-6 py-4 text-left text-xs font-bold text-slate-300 uppercase tracking-wider">
                    Current Stage
                  </th>
                  <th class="px-6 py-4 text-left text-xs font-bold text-slate-300 uppercase tracking-wider">
                    Status
                  </th>
                  <th class="px-6 py-4 text-left text-xs font-bold text-slate-300 uppercase tracking-wider">
                    Time in Stage
                  </th>
                </tr>
              </thead>
              <tbody class="bg-slate-900 divide-y divide-slate-800">
                <tr
                  v-for="job in activeJobs"
                  :key="job.job_id"
                  class="hover:bg-slate-800/50 transition-all duration-200"
                >
                  <td class="px-6 py-4 text-sm font-bold text-slate-100">
                    {{ job.job_title || 'Untitled' }}
                  </td>
                  <td class="px-6 py-4 text-sm font-semibold text-slate-200">
                    {{ job.company_name || 'Unknown' }}
                  </td>
                  <td class="px-6 py-4 text-sm">
                    <span class="inline-flex items-center px-3 py-1.5 bg-primary-900/30 text-primary-300 border border-primary-800 rounded-lg text-xs font-bold shadow-sm">
                      <Icon icon="heroicons:cog-6-tooth" class="w-4 h-4 mr-1.5" />
                      {{ job.current_stage || 'unknown' }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-sm">
                    <span class="inline-flex items-center px-3 py-1.5 bg-warning-900/30 text-warning-300 border border-warning-800 rounded-lg text-xs font-bold shadow-sm">
                      <span class="inline-block w-1.5 h-1.5 bg-warning-500 rounded-full mr-2 animate-pulse"></span>
                      {{ job.status || 'processing' }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-sm text-slate-300 font-medium">
                    <span class="flex items-center">
                      <Icon icon="heroicons:clock" class="w-4 h-4 mr-1.5" />
                      {{ job.time_in_stage || 'Just started' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Last Updated -->
        <div v-if="jobStore.pipeline.timestamp" class="mt-6 pt-6 border-t border-slate-800 flex items-center text-sm text-slate-400">
          <Icon icon="heroicons:clock" class="w-5 h-5 mr-2" />
          <span class="font-semibold mr-1">Last updated:</span>
          <span>{{ formatTime(jobStore.pipeline.timestamp) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Custom scrollbar for dark theme */
::-webkit-scrollbar {
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgb(15 23 42); /* slate-900 */
}

::-webkit-scrollbar-thumb {
  background: rgb(51 65 85); /* slate-700 */
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgb(71 85 105); /* slate-600 */
}
</style>
