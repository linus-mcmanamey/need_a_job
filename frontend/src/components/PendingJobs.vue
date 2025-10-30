<script setup>
import { useJobStore } from '../stores/jobStore'
import { ref } from 'vue'

// Get job store
const jobStore = useJobStore()

// Action loading states
const processingJobs = ref(new Set())

/**
 * Handle approve button click
 */
async function handleApprove(jobId) {
  processingJobs.value.add(jobId)

  try {
    await jobStore.approveJob(jobId)
  } catch (error) {
    console.error('Approve failed:', error)
  } finally {
    processingJobs.value.delete(jobId)
  }
}

/**
 * Handle reject button click
 */
async function handleReject(jobId) {
  processingJobs.value.add(jobId)

  try {
    await jobStore.rejectJob(jobId, 'User rejected from UI')
  } catch (error) {
    console.error('Reject failed:', error)
  } finally {
    processingJobs.value.delete(jobId)
  }
}

/**
 * Truncate long text
 */
function truncate(text, length = 150) {
  if (!text) return 'No description available'
  if (text.length <= length) return text
  return text.substring(0, length) + '...'
}
</script>

<template>
  <div>
    <!-- Loading State -->
    <div v-if="jobStore.loading.pending" class="text-center py-16">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-3 border-warning-600 border-t-3"></div>
      <p class="text-gray-600 mt-4 font-medium">Loading pending jobs...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="jobStore.pending.length === 0" class="text-center py-16 bg-gradient-to-br from-success-50 to-primary-50 rounded-xl border-2 border-dashed border-success-300">
      <span class="text-7xl mb-6 block animate-bounce">🎉</span>
      <h3 class="text-xl font-bold text-gray-800 mb-3">No pending jobs</h3>
      <p class="text-gray-600 max-w-md mx-auto">All jobs have been processed! Great work.</p>
    </div>

    <!-- Pending Jobs List -->
    <div v-else class="space-y-6">
      <div
        v-for="job in jobStore.pending"
        :key="job.job_id"
        class="group bg-white/90 backdrop-blur-sm border-2 border-gray-200 rounded-2xl p-8 hover:shadow-2xl hover:border-warning-300 transition-all duration-300 hover:-translate-y-1"
      >
        <!-- Job Header -->
        <div class="flex justify-between items-start mb-6">
          <div class="flex-1">
            <h4 class="text-2xl font-bold text-gray-900 group-hover:text-primary-600 transition-colors">
              {{ job.job_title || 'Untitled Job' }}
            </h4>
            <p class="text-base text-gray-600 mt-2 font-medium">
              {{ job.company_name || 'Unknown Company' }}
            </p>
            <div class="flex items-center gap-3 mt-3">
              <!-- Platform Badge -->
              <span
                v-if="job.platform_source"
                class="inline-flex items-center px-3 py-1.5 bg-primary-100 text-primary-700 rounded-lg text-xs font-bold border border-primary-200 shadow-sm"
              >
                <span class="mr-1.5">🔗</span>
                {{ job.platform_source }}
              </span>
              <!-- Status Badge -->
              <span
                :class="[
                  'inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-bold shadow-sm border',
                  job.status === 'pending'
                    ? 'bg-warning-100 text-warning-700 border-warning-200'
                    : 'bg-danger-100 text-danger-700 border-danger-200'
                ]"
              >
                <span v-if="job.status === 'pending'" class="mr-1.5 animate-pulse">⏳</span>
                <span v-else class="mr-1.5">⚠️</span>
                {{ job.status || 'pending' }}
              </span>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex gap-3 ml-6">
            <!-- Approve Button -->
            <button
              @click="handleApprove(job.job_id)"
              :disabled="processingJobs.has(job.job_id)"
              :class="[
                'px-6 py-3 rounded-xl font-bold transition-all duration-200 shadow-lg',
                processingJobs.has(job.job_id)
                  ? 'bg-gray-400 text-white cursor-not-allowed'
                  : 'bg-success-600 text-white hover:bg-success-700 hover:shadow-xl hover:scale-105 active:scale-95'
              ]"
            >
              <span v-if="processingJobs.has(job.job_id)" class="flex items-center">
                <span class="inline-block animate-spin mr-2">⏳</span>
                Processing...
              </span>
              <span v-else class="flex items-center">
                <span class="mr-2">✓</span>
                Approve
              </span>
            </button>

            <!-- Reject Button -->
            <button
              @click="handleReject(job.job_id)"
              :disabled="processingJobs.has(job.job_id)"
              :class="[
                'px-6 py-3 rounded-xl font-bold transition-all duration-200 shadow-lg',
                processingJobs.has(job.job_id)
                  ? 'bg-gray-400 text-white cursor-not-allowed'
                  : 'bg-danger-600 text-white hover:bg-danger-700 hover:shadow-xl hover:scale-105 active:scale-95'
              ]"
            >
              <span v-if="processingJobs.has(job.job_id)" class="flex items-center">
                <span class="inline-block animate-spin mr-2">⏳</span>
                Processing...
              </span>
              <span v-else class="flex items-center">
                <span class="mr-2">✗</span>
                Reject
              </span>
            </button>
          </div>
        </div>

        <!-- Job Details -->
        <div class="border-t-2 border-gray-100 pt-6 space-y-4">
          <!-- Current Stage -->
          <div v-if="job.current_stage" class="flex items-center">
            <span class="text-sm font-bold text-gray-700 mr-2">Current Stage:</span>
            <span class="inline-flex items-center px-3 py-1 bg-accent-100 text-accent-700 rounded-lg text-sm font-semibold border border-accent-200">
              <span class="mr-1.5">⚙️</span>
              {{ job.current_stage }}
            </span>
          </div>

          <!-- Error Info (for failed jobs) -->
          <div v-if="job.error_type || job.error_message" class="bg-danger-50 border-l-4 border-danger-500 rounded-lg p-4">
            <p class="text-sm font-bold text-danger-800 mb-2 flex items-center">
              <span class="mr-2">⚠️</span>
              Error: {{ job.error_type || 'Unknown Error' }}
            </p>
            <p class="text-sm text-danger-700 leading-relaxed">
              {{ job.error_message || 'No error details available' }}
            </p>
          </div>

          <!-- Job Description (truncated) -->
          <div v-if="job.job_description" class="bg-gray-50 rounded-lg p-4">
            <p class="font-bold text-gray-800 mb-2 flex items-center">
              <span class="mr-2">📝</span>
              Description:
            </p>
            <p class="text-sm text-gray-700 leading-relaxed">{{ truncate(job.job_description) }}</p>
          </div>

          <!-- Updated Time -->
          <div v-if="job.updated_at" class="flex items-center text-xs text-gray-500 pt-2">
            <span class="mr-2">🕐</span>
            <span class="font-medium">Last updated:</span>
            <span class="ml-1">{{ new Date(job.updated_at).toLocaleString() }}</span>
          </div>
        </div>
      </div>

      <!-- Pending Count -->
      <div class="mt-8 text-center py-6 bg-gradient-to-r from-warning-50 to-primary-50 rounded-xl border border-warning-200">
        <p class="text-base text-gray-700 font-bold flex items-center justify-center">
          <span class="inline-block w-2.5 h-2.5 bg-warning-500 rounded-full mr-2 animate-pulse"></span>
          {{ jobStore.pending.length }} job(s) requiring attention
        </p>
      </div>
    </div>
  </div>
</template>
