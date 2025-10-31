<script setup>
import { useJobStore } from '../stores/jobStore'
import { ref } from 'vue'

// Get job store
const jobStore = useJobStore()

// Retry loading state
const retryingJobs = ref(new Set())

/**
 * Get status badge color
 */
function getStatusColor(status) {
  const colors = {
    discovered: 'bg-gray-100 text-gray-700 border border-gray-200',
    matched: 'bg-primary-100 text-primary-700 border border-primary-200',
    documents_generated: 'bg-accent-100 text-accent-700 border border-accent-200',
    ready_to_send: 'bg-primary-100 text-primary-800 border border-primary-300',
    sending: 'bg-warning-100 text-warning-700 border border-warning-200',
    completed: 'bg-success-100 text-success-700 border border-success-200',
    pending: 'bg-warning-100 text-warning-700 border border-warning-200',
    failed: 'bg-danger-100 text-danger-700 border border-danger-200',
    rejected: 'bg-danger-100 text-danger-700 border border-danger-200',
    duplicate: 'bg-gray-100 text-gray-600 border border-gray-200',
  }
  return colors[status] || 'bg-gray-100 text-gray-700 border border-gray-200'
}

/**
 * Handle retry button click
 */
async function handleRetry(jobId) {
  retryingJobs.value.add(jobId)

  try {
    await jobStore.retryJob(jobId)
  } catch (error) {
    console.error('Retry failed:', error)
  } finally {
    retryingJobs.value.delete(jobId)
  }
}

/**
 * Check if job can be retried
 */
function canRetry(status) {
  return status === 'failed' || status === 'rejected' || status === 'pending'
}

/**
 * Calculate days since job was posted on the platform
 * Uses posted_date from the job site if available, otherwise falls back to discovered_timestamp
 */
function getDaysAdvertised(postedDate, discoveredTimestamp) {
  // Try to use posted_date first
  if (postedDate) {
    const posted = new Date(postedDate)
    const now = new Date()
    const diffMs = now - posted
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return '1 day'
    return `${diffDays} days`
  }

  // Fallback to discovered_timestamp
  if (!discoveredTimestamp) return 'N/A'

  const discovered = new Date(discoveredTimestamp)
  const now = new Date()
  const diffMs = now - discovered
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return '1 day'
  return `${diffDays} days`
}

/**
 * Get match score color
 */
function getScoreColor(score) {
  if (!score || score === 0) return 'text-gray-400'
  if (score >= 80) return 'text-green-600'
  if (score >= 60) return 'text-yellow-600'
  return 'text-red-600'
}
</script>

<template>
  <div>
    <!-- Loading State -->
    <div v-if="jobStore.loading.jobs" class="text-center py-16">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-3 border-primary-600 border-t-3"></div>
      <p class="text-gray-600 mt-4 font-medium">Loading jobs...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="jobStore.jobs.length === 0" class="text-center py-16 bg-gradient-to-br from-gray-50 to-primary-50 rounded-xl border-2 border-dashed border-gray-300">
      <span class="text-7xl mb-6 block animate-pulse-slow">📭</span>
      <h3 class="text-xl font-bold text-gray-800 mb-3">No jobs found</h3>
      <p class="text-gray-600 max-w-md mx-auto">Jobs will appear here once they are discovered from your configured job boards</p>
    </div>

    <!-- Jobs Table -->
    <div v-else class="overflow-hidden rounded-xl border border-gray-200">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gradient-to-r from-gray-50 to-gray-100">
            <tr>
              <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                Job Title
              </th>
              <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                Company
              </th>
              <th class="px-6 py-4 text-center text-xs font-bold text-gray-700 uppercase tracking-wider">
                Match Score
              </th>
              <th class="px-6 py-4 text-center text-xs font-bold text-gray-700 uppercase tracking-wider">
                Days Advertised
              </th>
              <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                Status
              </th>
              <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-100">
            <tr
              v-for="job in jobStore.jobs"
              :key="job.job_id"
              class="hover:bg-gradient-to-r hover:from-primary-50/30 hover:to-accent-50/30 transition-all duration-200"
            >
              <!-- Job Title -->
              <td class="px-6 py-4">
                <div class="text-sm font-bold text-gray-900">
                  {{ job.job_title || 'Untitled Job' }}
                </div>
                <div v-if="job.platform_source" class="flex items-center mt-2">
                  <a
                    v-if="job.job_url"
                    :href="job.job_url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="inline-flex items-center px-4 py-2 rounded-lg text-sm font-bold bg-blue-600 text-white border-2 border-blue-700 hover:bg-blue-700 hover:shadow-lg hover:scale-105 transition-all duration-200 active:scale-95 cursor-pointer shadow-md"
                  >
                    <span class="mr-2 text-base">🔗</span>
                    <span class="uppercase">{{ job.platform_source }}</span>
                  </a>
                  <span
                    v-else
                    class="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-100 text-gray-600 border border-gray-200"
                  >
                    <span class="mr-2">🔗</span>
                    {{ job.platform_source }}
                  </span>
                </div>
              </td>

              <!-- Company -->
              <td class="px-6 py-4">
                <div class="text-sm font-semibold text-gray-900">
                  {{ job.company_name || 'Unknown Company' }}
                </div>
              </td>

              <!-- Match Score -->
              <td class="px-6 py-4">
                <div class="flex items-center justify-center">
                  <span
                    :class="[
                      'text-2xl font-bold',
                      getScoreColor(job.match_score)
                    ]"
                  >
                    {{ job.match_score ? `${job.match_score}%` : 'N/A' }}
                  </span>
                </div>
              </td>

              <!-- Days Advertised -->
              <td class="px-6 py-4">
                <div class="text-center">
                  <span class="text-sm font-semibold text-gray-700">
                    {{ getDaysAdvertised(job.posted_date, job.discovered_timestamp) }}
                  </span>
                </div>
              </td>

              <!-- Status -->
              <td class="px-6 py-4">
                <span
                  :class="[
                    'px-3 py-1.5 inline-flex items-center text-xs leading-5 font-bold rounded-lg shadow-sm',
                    getStatusColor(job.status)
                  ]"
                >
                  {{ job.status || 'unknown' }}
                </span>
              </td>

              <!-- Actions -->
              <td class="px-6 py-4 text-sm">
                <button
                  v-if="canRetry(job.status)"
                  @click="handleRetry(job.job_id)"
                  :disabled="retryingJobs.has(job.job_id)"
                  :class="[
                    'px-4 py-2 rounded-lg font-semibold transition-all duration-200 shadow-sm',
                    retryingJobs.has(job.job_id)
                      ? 'bg-gray-400 text-white cursor-not-allowed'
                      : 'bg-primary-600 text-white hover:bg-primary-700 hover:shadow-md active:scale-95'
                  ]"
                >
                  <span v-if="retryingJobs.has(job.job_id)" class="flex items-center">
                    <span class="inline-block animate-spin mr-2">⏳</span>
                    Retrying...
                  </span>
                  <span v-else class="flex items-center">
                    <span class="mr-1.5">🔄</span>
                    Retry
                  </span>
                </button>
                <span v-else class="text-gray-400 text-sm font-medium">
                  No actions
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Job Count -->
      <div class="px-6 py-4 bg-gradient-to-r from-gray-50 to-gray-100 border-t border-gray-200">
        <p class="text-sm text-gray-700 font-semibold flex items-center">
          <span class="inline-block w-2 h-2 bg-primary-500 rounded-full mr-2"></span>
          Showing {{ jobStore.jobs.length }} job(s)
        </p>
      </div>
    </div>
  </div>
</template>
