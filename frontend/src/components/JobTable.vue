<script setup>
import { useJobStore } from '../stores/jobStore'
import { Icon } from '@iconify/vue'
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
    discovered: 'bg-slate-800 text-slate-300',
    matched: 'bg-primary-950/50 text-primary-400',
    documents_generated: 'bg-accent-950/50 text-accent-400',
    ready_to_send: 'bg-primary-950/50 text-primary-400',
    sending: 'bg-warning-950/50 text-warning-400',
    completed: 'bg-success-950/50 text-success-400',
    pending: 'bg-warning-950/50 text-warning-400',
    failed: 'bg-danger-950/50 text-danger-400',
    rejected: 'bg-danger-950/50 text-danger-400',
    duplicate: 'bg-slate-800 text-slate-400',
  }
  return colors[status] || 'bg-slate-800 text-slate-300'
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
  if (!score || score === 0) return 'text-slate-400'
  if (score >= 80) return 'text-success-400'
  if (score >= 60) return 'text-warning-400'
  return 'text-danger-400'
}
</script>

<template>
  <div>
    <!-- Loading State -->
    <div v-if="jobStore.loading.jobs" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-10 w-10 border-b-2 border-primary-500 border-t-2"></div>
      <p class="text-slate-400 mt-3 text-sm">Loading jobs...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="jobStore.jobs.length === 0" class="text-center py-12 rounded-lg border border-dashed border-slate-700">
      <Icon icon="heroicons:inbox" class="w-20 h-20 text-slate-600 mx-auto mb-4" />
      <h3 class="text-lg font-semibold text-slate-300 mb-2">No jobs found</h3>
      <p class="text-slate-500 text-sm max-w-md mx-auto">Jobs will appear here once they are discovered from your configured job boards</p>
    </div>

    <!-- Jobs Table -->
    <div v-else class="overflow-hidden rounded-lg border border-slate-800/50">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-800/50">
          <thead class="bg-slate-800/50">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wide">
                Job Title
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wide">
                Company
              </th>
              <th class="px-4 py-3 text-center text-xs font-medium text-slate-400 uppercase tracking-wide">
                Match Score
              </th>
              <th class="px-4 py-3 text-center text-xs font-medium text-slate-400 uppercase tracking-wide">
                Days Advertised
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wide">
                Status
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wide">
                Actions
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800/50">
            <tr
              v-for="job in jobStore.jobs"
              :key="job.job_id"
              class="hover:bg-slate-800/30 transition-colors duration-150"
            >
              <!-- Job Title -->
              <td class="px-4 py-3">
                <div class="text-sm font-semibold text-slate-100 mb-1">
                  {{ job.job_title || 'Untitled Job' }}
                </div>
                <div v-if="job.platform_source" class="flex items-center mt-1">
                  <a
                    v-if="job.job_url"
                    :href="job.job_url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="inline-flex items-center px-2.5 py-1 rounded text-xs font-medium bg-primary-600 text-white hover:bg-primary-500 transition-colors"
                  >
                    <Icon icon="heroicons:link" class="w-3 h-3 mr-1.5" />
                    <span>{{ job.platform_source }}</span>
                  </a>
                  <span
                    v-else
                    class="inline-flex items-center px-2.5 py-1 rounded text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700"
                  >
                    <Icon icon="heroicons:link" class="w-3 h-3 mr-1.5" />
                    <span>{{ job.platform_source }}</span>
                  </span>
                </div>
              </td>

              <!-- Company -->
              <td class="px-4 py-3">
                <div class="text-sm font-medium text-slate-200">
                  {{ job.company_name || 'Unknown Company' }}
                </div>
              </td>

              <!-- Match Score -->
              <td class="px-4 py-3">
                <div class="flex items-center justify-center">
                  <span
                    :class="[
                      'text-lg font-bold tabular-nums',
                      getScoreColor(job.match_score)
                    ]"
                  >
                    {{ job.match_score ? `${job.match_score}%` : 'N/A' }}
                  </span>
                </div>
              </td>

              <!-- Days Advertised -->
              <td class="px-4 py-3">
                <div class="text-center">
                  <span class="text-sm font-medium text-slate-300 tabular-nums">
                    {{ getDaysAdvertised(job.posted_date, job.discovered_timestamp) }}
                  </span>
                </div>
              </td>

              <!-- Status -->
              <td class="px-4 py-3">
                <span
                  :class="[
                    'px-2.5 py-1 inline-flex items-center text-xs font-medium rounded',
                    getStatusColor(job.status)
                  ]"
                >
                  {{ job.status || 'unknown' }}
                </span>
              </td>

              <!-- Actions -->
              <td class="px-4 py-3 text-sm">
                <button
                  v-if="canRetry(job.status)"
                  @click="handleRetry(job.job_id)"
                  :disabled="retryingJobs.has(job.job_id)"
                  :class="[
                    'px-3 py-1.5 rounded-lg font-medium text-xs transition-colors inline-flex items-center',
                    retryingJobs.has(job.job_id)
                      ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                      : 'bg-primary-600 text-white hover:bg-primary-500'
                  ]"
                >
                  <span v-if="retryingJobs.has(job.job_id)" class="flex items-center">
                    <Icon icon="heroicons:clock" class="w-4 h-4 mr-1.5 animate-spin" />
                    Retrying...
                  </span>
                  <span v-else class="flex items-center">
                    <Icon icon="heroicons:arrow-path" class="w-4 h-4 mr-1.5" />
                    Retry
                  </span>
                </button>
                <span v-else class="text-slate-500 text-xs font-medium">
                  -
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Job Count -->
      <div class="px-4 py-3 bg-slate-800/30 border-t border-slate-800/50">
        <p class="text-xs text-slate-400 font-medium">
          Showing <span class="text-slate-200 font-semibold">{{ jobStore.jobs.length }}</span> job(s)
        </p>
      </div>
    </div>
  </div>
</template>
