<script setup>
import { computed, watch, onMounted, onUnmounted } from 'vue'
import { Icon } from '@iconify/vue'

const props = defineProps({
  application: {
    type: Object,
    default: null,
  },
  isOpen: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close'])

/**
 * Close modal
 */
function closeModal() {
  emit('close')
}

/**
 * Handle escape key press
 */
function handleEscape(event) {
  if (event.key === 'Escape' && props.isOpen) {
    closeModal()
  }
}

/**
 * Handle backdrop click
 */
function handleBackdropClick(event) {
  if (event.target === event.currentTarget) {
    closeModal()
  }
}

/**
 * Get status color
 */
function getStatusColor(status) {
  const colors = {
    completed: 'bg-success-100 text-success-700 border border-success-200',
    rejected: 'bg-danger-100 text-danger-700 border border-danger-200',
    pending: 'bg-warning-100 text-warning-700 border border-warning-200',
  }
  return colors[status] || 'bg-gray-100 text-gray-700 border border-gray-200'
}

/**
 * Get platform icon
 */
function getPlatformIcon(platform) {
  const icons = {
    linkedin: 'heroicons:briefcase',
    seek: 'heroicons:magnifying-glass',
    indeed: 'heroicons:map-pin',
  }
  return icons[platform] || 'heroicons:link'
}

/**
 * Format date for display
 */
function formatDate(dateString) {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

/**
 * Format salary
 */
function formatSalary(salary) {
  if (!salary) return 'Not specified'
  return `$${salary.toFixed(2)} AUD/day`
}

/**
 * Get match score color class
 */
const matchScoreColorClass = computed(() => {
  if (!props.application?.match_score) return 'text-gray-500'
  const score = props.application.match_score
  if (score >= 80) return 'text-success-500'
  if (score >= 60) return 'text-warning-500'
  return 'text-danger-500'
})

/**
 * Get match score progress color
 */
const matchScoreProgressColor = computed(() => {
  if (!props.application?.match_score) return 'bg-gray-500'
  const score = props.application.match_score
  if (score >= 80) return 'bg-success-500'
  if (score >= 60) return 'bg-warning-500'
  return 'bg-danger-500'
})

// Setup/cleanup keyboard listener
onMounted(() => {
  document.addEventListener('keydown', handleEscape)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscape)
})

// Prevent body scroll when modal is open
watch(
  () => props.isOpen,
  (isOpen) => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
  }
)
</script>

<template>
  <!-- Modal Backdrop -->
  <Transition name="modal-backdrop">
    <div
      v-if="isOpen && application"
      @click="handleBackdropClick"
      class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
    >
      <!-- Modal Container -->
      <Transition name="modal-content">
        <div
          v-if="isOpen"
          class="bg-slate-900 rounded-2xl shadow-2xl border border-slate-700 max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col"
          @click.stop
        >
          <!-- Modal Header -->
          <div class="bg-gradient-to-r from-slate-900 to-slate-800 px-6 py-5 border-b border-slate-700 flex items-center justify-between">
            <div class="flex-1">
              <h2 class="text-2xl font-bold text-slate-50 mb-1">
                {{ application.job_title || 'Application Details' }}
              </h2>
              <p class="text-slate-400 text-sm">
                {{ application.company_name || 'Unknown Company' }}
              </p>
            </div>
            <button
              @click="closeModal"
              class="ml-4 p-2 rounded-lg hover:bg-slate-700 transition-colors text-slate-400 hover:text-slate-200"
              aria-label="Close modal"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Modal Body -->
          <div class="flex-1 overflow-y-auto p-6 space-y-6">
            <!-- Quick Stats -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <!-- Platform -->
              <div class="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                <p class="text-xs text-slate-400 mb-1 font-medium">Platform</p>
                <div class="flex items-center">
                  <Icon :icon="getPlatformIcon(application.platform)" class="w-6 h-6 mr-2 text-slate-300" />
                  <span class="text-slate-100 font-semibold capitalize">{{ application.platform }}</span>
                </div>
              </div>

              <!-- Status -->
              <div class="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                <p class="text-xs text-slate-400 mb-2 font-medium">Status</p>
                <span
                  :class="[
                    'px-3 py-1.5 inline-flex items-center text-xs leading-5 font-bold rounded-lg',
                    getStatusColor(application.status)
                  ]"
                >
                  {{ application.status }}
                </span>
              </div>

              <!-- Match Score -->
              <div class="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                <p class="text-xs text-slate-400 mb-1 font-medium">Match Score</p>
                <div class="flex items-center">
                  <span :class="['text-3xl font-bold mr-2', matchScoreColorClass]">
                    {{ application.match_score || 0 }}%
                  </span>
                </div>
                <div class="mt-2 w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    :style="{ width: (application.match_score || 0) + '%' }"
                    :class="['h-full transition-all', matchScoreProgressColor]"
                  ></div>
                </div>
              </div>

              <!-- Applied Date -->
              <div class="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                <p class="text-xs text-slate-400 mb-1 font-medium">Applied Date</p>
                <p class="text-slate-100 font-semibold text-sm">
                  {{ formatDate(application.applied_date) }}
                </p>
              </div>
            </div>

            <!-- Job Information -->
            <div class="bg-slate-800/50 rounded-lg p-5 border border-slate-700">
              <h3 class="text-lg font-bold text-slate-50 mb-4 flex items-center">
                <Icon icon="heroicons:clipboard-document-list" class="w-5 h-5 mr-2" />
                Job Information
              </h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p class="text-xs text-slate-400 mb-1 font-medium">Location</p>
                  <p class="text-slate-100">{{ application.location || 'Not specified' }}</p>
                </div>
                <div>
                  <p class="text-xs text-slate-400 mb-1 font-medium">Salary</p>
                  <p class="text-slate-100">{{ formatSalary(application.salary_aud_per_day) }}</p>
                </div>
                <div class="md:col-span-2">
                  <p class="text-xs text-slate-400 mb-1 font-medium">Job URL</p>
                  <a
                    v-if="application.job_url"
                    :href="application.job_url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="text-primary-400 hover:text-primary-300 underline break-all text-sm"
                  >
                    {{ application.job_url }}
                  </a>
                  <p v-else class="text-slate-400 text-sm">Not available</p>
                </div>
              </div>
            </div>

            <!-- Job Description -->
            <div v-if="application.job_description" class="bg-slate-800/50 rounded-lg p-5 border border-slate-700">
              <h3 class="text-lg font-bold text-slate-50 mb-3 flex items-center">
                <Icon icon="heroicons:document-text" class="w-5 h-5 mr-2" />
                Job Description
              </h3>
              <div class="prose prose-invert prose-sm max-w-none">
                <p class="text-slate-300 whitespace-pre-wrap leading-relaxed">
                  {{ application.job_description }}
                </p>
              </div>
            </div>

            <!-- Application Documents -->
            <div class="bg-slate-800/50 rounded-lg p-5 border border-slate-700">
              <h3 class="text-lg font-bold text-slate-50 mb-4 flex items-center">
                <Icon icon="heroicons:paper-clip" class="w-5 h-5 mr-2" />
                Application Documents
              </h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <!-- CV -->
                <div class="flex items-center justify-between p-4 bg-slate-900 rounded-lg border border-slate-700">
                  <div class="flex items-center">
                    <Icon icon="heroicons:document" class="w-8 h-8 text-slate-400 mr-3" />
                    <div>
                      <p class="text-sm font-semibold text-slate-100">Resume / CV</p>
                      <p class="text-xs text-slate-400 mt-0.5">
                        {{ application.cv_file_path ? 'Available' : 'Not available' }}
                      </p>
                    </div>
                  </div>
                  <a
                    v-if="application.cv_file_path"
                    :href="`/api/applications/${application.application_id}/cv`"
                    download
                    class="px-3 py-1.5 bg-primary-600 text-white rounded-lg text-xs font-semibold hover:bg-primary-700 transition-colors"
                  >
                    Download
                  </a>
                  <span v-else class="text-xs text-slate-500">N/A</span>
                </div>

                <!-- Cover Letter -->
                <div class="flex items-center justify-between p-4 bg-slate-900 rounded-lg border border-slate-700">
                  <div class="flex items-center">
                    <Icon icon="heroicons:envelope" class="w-8 h-8 text-slate-400 mr-3" />
                    <div>
                      <p class="text-sm font-semibold text-slate-100">Cover Letter</p>
                      <p class="text-xs text-slate-400 mt-0.5">
                        {{ application.cl_file_path ? 'Available' : 'Not available' }}
                      </p>
                    </div>
                  </div>
                  <a
                    v-if="application.cl_file_path"
                    :href="`/api/applications/${application.application_id}/cl`"
                    download
                    class="px-3 py-1.5 bg-primary-600 text-white rounded-lg text-xs font-semibold hover:bg-primary-700 transition-colors"
                  >
                    Download
                  </a>
                  <span v-else class="text-xs text-slate-500">N/A</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Modal Footer -->
          <div class="bg-gradient-to-r from-slate-900 to-slate-800 px-6 py-4 border-t border-slate-700 flex justify-end">
            <button
              @click="closeModal"
              class="px-6 py-2.5 bg-slate-700 text-slate-200 rounded-lg font-semibold hover:bg-slate-600 transition-all duration-200"
            >
              Close
            </button>
          </div>
        </div>
      </Transition>
    </div>
  </Transition>
</template>

<style scoped>
/* Modal backdrop transition */
.modal-backdrop-enter-active {
  transition: opacity 0.3s ease;
}

.modal-backdrop-leave-active {
  transition: opacity 0.2s ease;
}

.modal-backdrop-enter-from,
.modal-backdrop-leave-to {
  opacity: 0;
}

/* Modal content transition */
.modal-content-enter-active {
  transition: all 0.3s ease;
}

.modal-content-leave-active {
  transition: all 0.2s ease;
}

.modal-content-enter-from {
  opacity: 0;
  transform: scale(0.9) translateY(-20px);
}

.modal-content-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* Custom scrollbar for modal */
.overflow-y-auto::-webkit-scrollbar {
  width: 8px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: rgb(15 23 42); /* slate-900 */
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: rgb(51 65 85); /* slate-700 */
  border-radius: 4px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: rgb(71 85 105); /* slate-600 */
}
</style>
