<script setup>
import { useJobStore } from '../stores/jobStore'
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
      color: 'bg-gradient-to-br from-primary-100 to-primary-200',
      textColor: 'text-primary-700',
      borderColor: 'border-primary-200',
      icon: '🔍',
    },
    {
      label: 'Active Processing',
      count: Object.values(counts).reduce((sum, val) => {
        return sum + (typeof val === 'number' ? val : 0)
      }, 0) - (counts.completed || 0) - (counts.rejected || 0),
      color: 'bg-gradient-to-br from-accent-100 to-accent-200',
      textColor: 'text-accent-700',
      borderColor: 'border-accent-200',
      icon: '⚙️',
    },
    {
      label: 'Completed',
      count: counts.completed || 0,
      color: 'bg-gradient-to-br from-success-100 to-success-200',
      textColor: 'text-success-700',
      borderColor: 'border-success-200',
      icon: '✅',
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
  <div>
    <!-- Loading State -->
    <div v-if="jobStore.loading.pipeline" class="text-center py-16">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-3 border-accent-600 border-t-3"></div>
      <p class="text-gray-600 mt-4 font-medium">Loading pipeline metrics...</p>
    </div>

    <!-- Pipeline Content -->
    <div v-else>
      <!-- Metrics Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div
          v-for="metric in metrics"
          :key="metric.label"
          :class="['group bg-white/90 backdrop-blur-sm border-2 rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1', metric.borderColor]"
        >
          <div class="flex items-center justify-between">
            <div>
              <p class="text-gray-600 text-sm font-bold uppercase tracking-wider">{{ metric.label }}</p>
              <p :class="['text-4xl font-bold mt-3 transition-colors', metric.textColor]">
                {{ metric.count }}
              </p>
            </div>
            <div :class="['rounded-2xl p-4 group-hover:scale-110 transition-transform duration-300', metric.color]">
              <span class="text-3xl">{{ metric.icon }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Active Jobs Section -->
      <div class="bg-white/90 backdrop-blur-sm border-2 border-gray-200 rounded-2xl p-8 shadow-lg">
        <h3 class="text-2xl font-bold text-gray-900 mb-6 flex items-center">
          <span class="mr-3 text-3xl">📊</span>
          Active Jobs in Pipeline
        </h3>

        <!-- Empty State -->
        <div v-if="activeJobs.length === 0" class="text-center py-12 bg-gradient-to-br from-gray-50 to-accent-50 rounded-xl border-2 border-dashed border-gray-300">
          <span class="text-6xl mb-4 block animate-pulse-slow">🎯</span>
          <h4 class="text-lg font-bold text-gray-800 mb-2">No Active Jobs</h4>
          <p class="text-gray-600">No jobs currently being processed in the pipeline</p>
        </div>

        <!-- Active Jobs Table -->
        <div v-else class="overflow-hidden rounded-xl border border-gray-200">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gradient-to-r from-gray-50 to-gray-100">
                <tr>
                  <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                    Job
                  </th>
                  <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                    Company
                  </th>
                  <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                    Current Stage
                  </th>
                  <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                    Status
                  </th>
                  <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                    Time in Stage
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-100">
                <tr
                  v-for="job in activeJobs"
                  :key="job.job_id"
                  class="hover:bg-gradient-to-r hover:from-accent-50/30 hover:to-primary-50/30 transition-all duration-200"
                >
                  <td class="px-6 py-4 text-sm font-bold text-gray-900">
                    {{ job.job_title || 'Untitled' }}
                  </td>
                  <td class="px-6 py-4 text-sm font-semibold text-gray-700">
                    {{ job.company_name || 'Unknown' }}
                  </td>
                  <td class="px-6 py-4 text-sm">
                    <span class="inline-flex items-center px-3 py-1.5 bg-primary-100 text-primary-700 rounded-lg text-xs font-bold border border-primary-200 shadow-sm">
                      <span class="mr-1.5">⚙️</span>
                      {{ job.current_stage || 'unknown' }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-sm">
                    <span class="inline-flex items-center px-3 py-1.5 bg-warning-100 text-warning-700 rounded-lg text-xs font-bold border border-warning-200 shadow-sm">
                      <span class="inline-block w-1.5 h-1.5 bg-warning-500 rounded-full mr-2 animate-pulse"></span>
                      {{ job.status || 'processing' }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-sm text-gray-600 font-medium">
                    <span class="flex items-center">
                      <span class="mr-1.5">🕐</span>
                      {{ job.time_in_stage || 'Just started' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Last Updated -->
        <div v-if="jobStore.pipeline.timestamp" class="mt-6 pt-6 border-t-2 border-gray-100 flex items-center text-sm text-gray-600">
          <span class="mr-2 text-lg">🕐</span>
          <span class="font-semibold mr-1">Last updated:</span>
          <span>{{ formatTime(jobStore.pipeline.timestamp) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
