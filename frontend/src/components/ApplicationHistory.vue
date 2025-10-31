<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useHistoryStore } from '../stores/historyStore'
import ApplicationDetailModal from './ApplicationDetailModal.vue'
import PlatformDistributionChart from './PlatformDistributionChart.vue'
import ApplicationTrendChart from './ApplicationTrendChart.vue'

// Get history store
const historyStore = useHistoryStore()

// Modal state
const selectedApplication = ref(null)
const isModalOpen = ref(false)

// Local filter state (bound to UI inputs)
const searchQuery = ref('')
const selectedPlatforms = ref([])
const selectedStatuses = ref([])
const dateFrom = ref('')
const dateTo = ref('')
const scoreRange = ref([0, 100])

// Sort state
const currentSortColumn = ref('applied_date')
const currentSortOrder = ref('desc')

// Filter options
const platformOptions = [
  { value: 'linkedin', label: 'LinkedIn', icon: '💼' },
  { value: 'seek', label: 'SEEK', icon: '🔍' },
  { value: 'indeed', label: 'Indeed', icon: '📍' },
]

const statusOptions = [
  { value: 'completed', label: 'Completed', color: 'success' },
  { value: 'rejected', label: 'Rejected', color: 'danger' },
  { value: 'pending', label: 'Pending', color: 'warning' },
]

// Sortable columns
const sortableColumns = [
  { key: 'applied_date', label: 'Applied Date' },
  { key: 'title', label: 'Job Title' },
  { key: 'company', label: 'Company' },
  { key: 'platform', label: 'Platform' },
  { key: 'match_score', label: 'Score' },
  { key: 'status', label: 'Status' },
]

/**
 * Get status badge color
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
    linkedin: '💼',
    seek: '🔍',
    indeed: '📍',
  }
  return icons[platform] || '🔗'
}

/**
 * Format date for display
 */
function formatDate(dateString) {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

/**
 * Handle sort column click
 */
async function handleSort(columnKey) {
  if (currentSortColumn.value === columnKey) {
    // Toggle order
    currentSortOrder.value = currentSortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    // New column, default desc
    currentSortColumn.value = columnKey
    currentSortOrder.value = 'desc'
  }

  await historyStore.updateSort(currentSortColumn.value, currentSortOrder.value)
}

/**
 * Apply filters
 */
async function applyFilters() {
  // Update historyStore filters with debounce
  await historyStore.updateFilters({
    search: searchQuery.value,
    platform: selectedPlatforms.value,
    status: selectedStatuses.value,
    dateRange: {
      start: dateFrom.value || null,
      end: dateTo.value || null,
    },
    scoreRange: scoreRange.value,
  })
}

/**
 * Clear all filters
 */
async function clearAllFilters() {
  searchQuery.value = ''
  selectedPlatforms.value = []
  selectedStatuses.value = []
  dateFrom.value = ''
  dateTo.value = ''
  scoreRange.value = [0, 100]

  await historyStore.clearFilters()
}

/**
 * Toggle platform filter
 */
function togglePlatform(platform) {
  const index = selectedPlatforms.value.indexOf(platform)
  if (index > -1) {
    selectedPlatforms.value.splice(index, 1)
  } else {
    selectedPlatforms.value.push(platform)
  }
  applyFilters()
}

/**
 * Toggle status filter
 */
function toggleStatus(status) {
  const index = selectedStatuses.value.indexOf(status)
  if (index > -1) {
    selectedStatuses.value.splice(index, 1)
  } else {
    selectedStatuses.value.push(status)
  }
  applyFilters()
}

/**
 * Check if filters are active
 */
const hasActiveFilters = computed(() => {
  return (
    searchQuery.value ||
    selectedPlatforms.value.length > 0 ||
    selectedStatuses.value.length > 0 ||
    dateFrom.value ||
    dateTo.value ||
    scoreRange.value[0] > 0 ||
    scoreRange.value[1] < 100
  )
})

/**
 * Get sort icon for column
 */
function getSortIcon(columnKey) {
  if (currentSortColumn.value !== columnKey) {
    return '⇅' // Both arrows (not sorted)
  }
  return currentSortOrder.value === 'asc' ? '↑' : '↓'
}

/**
 * Open detail modal for an application
 */
function openDetailModal(application) {
  selectedApplication.value = application
  isModalOpen.value = true
}

/**
 * Close detail modal
 */
function closeDetailModal() {
  isModalOpen.value = false
  // Delay clearing the application to allow transition to complete
  setTimeout(() => {
    selectedApplication.value = null
  }, 300)
}

/**
 * Go to specific page
 */
function goToPage(page) {
  historyStore.setPage(page)
  // Scroll to top of table
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

/**
 * Go to previous page
 */
function previousPage() {
  if (historyStore.pagination.page > 1) {
    goToPage(historyStore.pagination.page - 1)
  }
}

/**
 * Go to next page
 */
function nextPage() {
  if (historyStore.pagination.page < historyStore.totalPages) {
    goToPage(historyStore.pagination.page + 1)
  }
}

/**
 * Get page numbers to display in pagination
 * Shows: 1, ..., current-1, current, current+1, ..., last
 */
const pageNumbers = computed(() => {
  const total = historyStore.totalPages
  const current = historyStore.pagination.page
  const pages = []

  if (total <= 7) {
    // Show all pages if 7 or fewer
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    // Always show first page
    pages.push(1)

    // Show ellipsis if needed
    if (current > 3) {
      pages.push('...')
    }

    // Show pages around current page
    const start = Math.max(2, current - 1)
    const end = Math.min(total - 1, current + 1)

    for (let i = start; i <= end; i++) {
      pages.push(i)
    }

    // Show ellipsis if needed
    if (current < total - 2) {
      pages.push('...')
    }

    // Always show last page
    pages.push(total)
  }

  return pages
})

/**
 * Read filters from URL query parameters
 */
function readFiltersFromURL() {
  const params = new URLSearchParams(window.location.search)

  // Read search query
  const search = params.get('search')
  if (search) {
    searchQuery.value = search
  }

  // Read platforms (comma-separated)
  const platforms = params.get('platforms')
  if (platforms) {
    selectedPlatforms.value = platforms.split(',').filter(Boolean)
  }

  // Read statuses (comma-separated)
  const statuses = params.get('statuses')
  if (statuses) {
    selectedStatuses.value = statuses.split(',').filter(Boolean)
  }

  // Read date range
  const dateFromParam = params.get('dateFrom')
  if (dateFromParam) {
    dateFrom.value = dateFromParam
  }

  const dateToParam = params.get('dateTo')
  if (dateToParam) {
    dateTo.value = dateToParam
  }

  // Read score range
  const scoreMin = params.get('scoreMin')
  const scoreMax = params.get('scoreMax')
  if (scoreMin !== null || scoreMax !== null) {
    scoreRange.value = [
      scoreMin !== null ? parseInt(scoreMin, 10) : 0,
      scoreMax !== null ? parseInt(scoreMax, 10) : 100,
    ]
  }

  // Read sort column and order
  const sortBy = params.get('sortBy')
  if (sortBy) {
    currentSortColumn.value = sortBy
  }

  const sortOrder = params.get('sortOrder')
  if (sortOrder && (sortOrder === 'asc' || sortOrder === 'desc')) {
    currentSortOrder.value = sortOrder
  }

  console.log('[ApplicationHistory] Filters loaded from URL:', {
    search: searchQuery.value,
    platforms: selectedPlatforms.value,
    statuses: selectedStatuses.value,
    dateFrom: dateFrom.value,
    dateTo: dateTo.value,
    scoreRange: scoreRange.value,
    sortBy: currentSortColumn.value,
    sortOrder: currentSortOrder.value,
  })
}

/**
 * Update URL query parameters with current filter state
 */
function updateURLParams() {
  const params = new URLSearchParams()

  // Add search query
  if (searchQuery.value) {
    params.set('search', searchQuery.value)
  }

  // Add platforms
  if (selectedPlatforms.value.length > 0) {
    params.set('platforms', selectedPlatforms.value.join(','))
  }

  // Add statuses
  if (selectedStatuses.value.length > 0) {
    params.set('statuses', selectedStatuses.value.join(','))
  }

  // Add date range
  if (dateFrom.value) {
    params.set('dateFrom', dateFrom.value)
  }
  if (dateTo.value) {
    params.set('dateTo', dateTo.value)
  }

  // Add score range (only if not default)
  if (scoreRange.value[0] > 0) {
    params.set('scoreMin', scoreRange.value[0].toString())
  }
  if (scoreRange.value[1] < 100) {
    params.set('scoreMax', scoreRange.value[1].toString())
  }

  // Add sort params (only if not default)
  if (currentSortColumn.value !== 'applied_date') {
    params.set('sortBy', currentSortColumn.value)
  }
  if (currentSortOrder.value !== 'desc') {
    params.set('sortOrder', currentSortOrder.value)
  }

  // Update URL without reloading page
  const newURL = params.toString()
    ? `${window.location.pathname}?${params.toString()}`
    : window.location.pathname

  window.history.pushState({}, '', newURL)

  console.log('[ApplicationHistory] URL updated with filters')
}

/**
 * Handle browser back/forward navigation
 */
function handlePopState() {
  console.log('[ApplicationHistory] Browser navigation detected, reading filters from URL')
  readFiltersFromURL()
  applyFilters()
}

// Initialize on mount
onMounted(async () => {
  console.log('[ApplicationHistory] Component mounted, initializing store')

  // Read filters from URL first
  readFiltersFromURL()

  // Initialize store with URL params
  await historyStore.initialize()

  // Apply filters if any were loaded from URL
  if (hasActiveFilters.value) {
    await applyFilters()
  }

  // Update sort if loaded from URL
  if (currentSortColumn.value !== 'applied_date' || currentSortOrder.value !== 'desc') {
    await historyStore.updateSort(currentSortColumn.value, currentSortOrder.value)
  }

  // Listen for browser back/forward navigation
  window.addEventListener('popstate', handlePopState)
})

// Cleanup on unmount
onUnmounted(() => {
  console.log('[ApplicationHistory] Component unmounting, cleaning up')
  window.removeEventListener('popstate', handlePopState)
})

// Watch filters and update URL whenever they change
watch(
  [searchQuery, selectedPlatforms, selectedStatuses, dateFrom, dateTo, scoreRange, currentSortColumn, currentSortOrder],
  () => {
    updateURLParams()
  },
  { deep: true }
)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-3xl font-bold text-slate-50">Application History</h2>
        <p class="text-slate-400 mt-1">
          {{ historyStore.statistics.total }} applications tracked
        </p>
      </div>

      <!-- Export Button -->
      <button
        @click="historyStore.downloadCSV"
        :disabled="historyStore.filteredApplications.length === 0"
        class="px-4 py-2 bg-accent-600 text-white rounded-lg font-semibold hover:bg-accent-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center shadow-lg"
      >
        <span class="mr-2">📥</span>
        Export CSV
      </button>
    </div>

    <!-- Statistics Dashboard -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
      <!-- Total Applications -->
      <div class="bg-gradient-to-br from-blue-900/40 to-blue-800/20 rounded-xl border border-blue-800 p-6">
        <div class="flex items-center justify-between mb-2">
          <span class="text-blue-300 text-sm font-medium">Total Applications</span>
          <span class="text-3xl">📊</span>
        </div>
        <p class="text-4xl font-bold text-blue-100">{{ historyStore.statistics.total }}</p>
      </div>

      <!-- This Week -->
      <div class="bg-gradient-to-br from-green-900/40 to-green-800/20 rounded-xl border border-green-800 p-6">
        <div class="flex items-center justify-between mb-2">
          <span class="text-green-300 text-sm font-medium">This Week</span>
          <span class="text-3xl">📅</span>
        </div>
        <p class="text-4xl font-bold text-green-100">{{ historyStore.statistics.thisWeek }}</p>
      </div>

      <!-- This Month -->
      <div class="bg-gradient-to-br from-purple-900/40 to-purple-800/20 rounded-xl border border-purple-800 p-6">
        <div class="flex items-center justify-between mb-2">
          <span class="text-purple-300 text-sm font-medium">This Month</span>
          <span class="text-3xl">📆</span>
        </div>
        <p class="text-4xl font-bold text-purple-100">{{ historyStore.statistics.thisMonth }}</p>
      </div>

      <!-- Average Match Score -->
      <div class="bg-gradient-to-br from-yellow-900/40 to-yellow-800/20 rounded-xl border border-yellow-800 p-6">
        <div class="flex items-center justify-between mb-2">
          <span class="text-yellow-300 text-sm font-medium">Avg Match Score</span>
          <span class="text-3xl">⭐</span>
        </div>
        <p class="text-4xl font-bold text-yellow-100">{{ historyStore.statistics.avgMatchScore }}%</p>
      </div>

      <!-- Success Rate -->
      <div class="bg-gradient-to-br from-emerald-900/40 to-emerald-800/20 rounded-xl border border-emerald-800 p-6">
        <div class="flex items-center justify-between mb-2">
          <span class="text-emerald-300 text-sm font-medium">Success Rate</span>
          <span class="text-3xl">🎯</span>
        </div>
        <p class="text-4xl font-bold text-emerald-100">{{ historyStore.statistics.successRate }}%</p>
      </div>
    </div>

    <!-- Charts Section -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <!-- Platform Distribution Chart -->
      <div class="bg-slate-900/50 rounded-xl border border-slate-800 p-6">
        <h3 class="text-xl font-bold text-slate-100 mb-4 flex items-center">
          <span class="mr-2">📊</span>
          Platform Distribution
        </h3>
        <div class="h-64">
          <PlatformDistributionChart
            :platform-distribution="historyStore.statistics.platformDistribution"
          />
        </div>
      </div>

      <!-- Application Trend Chart -->
      <div class="bg-slate-900/50 rounded-xl border border-slate-800 p-6">
        <h3 class="text-xl font-bold text-slate-100 mb-4 flex items-center">
          <span class="mr-2">📈</span>
          Application Trend (Last 12 Weeks)
        </h3>
        <div class="h-64">
          <ApplicationTrendChart
            :applications="historyStore.applications"
          />
        </div>
      </div>
    </div>

    <!-- Filters Section -->
    <div class="bg-slate-900/50 rounded-xl border border-slate-800 p-6 space-y-6">
      <!-- Search Bar -->
      <div>
        <label class="block text-sm font-medium text-slate-300 mb-2">
          Search
        </label>
        <input
          v-model="searchQuery"
          @input="applyFilters"
          type="text"
          placeholder="Search by job title or company..."
          class="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
        />
      </div>

      <!-- Platform Filters -->
      <div>
        <label class="block text-sm font-medium text-slate-300 mb-3">
          Platform
        </label>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="option in platformOptions"
            :key="option.value"
            @click="togglePlatform(option.value)"
            :class="[
              'px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center',
              selectedPlatforms.includes(option.value)
                ? 'bg-primary-600 text-white shadow-md'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700',
            ]"
          >
            <span class="mr-2">{{ option.icon }}</span>
            {{ option.label }}
          </button>
        </div>
      </div>

      <!-- Status Filters -->
      <div>
        <label class="block text-sm font-medium text-slate-300 mb-3">
          Status
        </label>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="option in statusOptions"
            :key="option.value"
            @click="toggleStatus(option.value)"
            :class="[
              'px-4 py-2 rounded-lg font-medium transition-all duration-200',
              selectedStatuses.includes(option.value)
                ? `bg-${option.color}-600 text-white shadow-md`
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700',
            ]"
          >
            {{ option.label }}
          </button>
        </div>
      </div>

      <!-- Date Range -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-slate-300 mb-2">
            From Date
          </label>
          <input
            v-model="dateFrom"
            @change="applyFilters"
            type="date"
            class="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-300 mb-2">
            To Date
          </label>
          <input
            v-model="dateTo"
            @change="applyFilters"
            type="date"
            class="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
          />
        </div>
      </div>

      <!-- Match Score Range -->
      <div>
        <label class="block text-sm font-medium text-slate-300 mb-2">
          Match Score Range: {{ scoreRange[0] }} - {{ scoreRange[1] }}
        </label>
        <div class="flex items-center gap-4">
          <input
            v-model.number="scoreRange[0]"
            @change="applyFilters"
            type="range"
            min="0"
            max="100"
            class="flex-1"
          />
          <input
            v-model.number="scoreRange[1]"
            @change="applyFilters"
            type="range"
            min="0"
            max="100"
            class="flex-1"
          />
        </div>
      </div>

      <!-- Clear Filters Button -->
      <div v-if="hasActiveFilters" class="flex justify-end">
        <button
          @click="clearAllFilters"
          class="px-4 py-2 bg-slate-700 text-slate-200 rounded-lg font-medium hover:bg-slate-600 transition-all duration-200"
        >
          Clear All Filters
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="historyStore.loading" class="text-center py-16">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-3 border-primary-600 border-t-3"></div>
      <p class="text-slate-400 mt-4 font-medium">Loading application history...</p>
    </div>

    <!-- Empty State -->
    <div
      v-else-if="historyStore.filteredApplications.length === 0"
      class="text-center py-16 bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl border-2 border-dashed border-slate-700"
    >
      <span class="text-7xl mb-6 block">📭</span>
      <h3 class="text-xl font-bold text-slate-200 mb-3">No applications found</h3>
      <p class="text-slate-400 max-w-md mx-auto">
        {{ hasActiveFilters ? 'Try adjusting your filters' : 'Applications will appear here once you start applying to jobs' }}
      </p>
    </div>

    <!-- Applications Table -->
    <div v-else class="overflow-hidden rounded-xl border border-slate-800">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-slate-800">
          <thead class="bg-gradient-to-r from-slate-900 to-slate-800">
            <tr>
              <th
                v-for="column in sortableColumns"
                :key="column.key"
                @click="handleSort(column.key)"
                class="px-6 py-4 text-left text-xs font-bold text-slate-300 uppercase tracking-wider cursor-pointer hover:bg-slate-700 transition-colors"
              >
                <div class="flex items-center justify-between">
                  {{ column.label }}
                  <span class="ml-2 text-slate-500">{{ getSortIcon(column.key) }}</span>
                </div>
              </th>
            </tr>
          </thead>
          <tbody class="bg-slate-900 divide-y divide-slate-800">
            <tr
              v-for="app in historyStore.paginatedApplications"
              :key="app.application_id"
              @click="openDetailModal(app)"
              class="hover:bg-slate-800/50 transition-all duration-200 cursor-pointer"
            >
              <!-- Applied Date -->
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-slate-200">
                  {{ formatDate(app.applied_date) }}
                </div>
              </td>

              <!-- Job Title -->
              <td class="px-6 py-4">
                <div class="text-sm font-bold text-slate-100">
                  {{ app.job_title || 'Untitled Job' }}
                </div>
              </td>

              <!-- Company -->
              <td class="px-6 py-4">
                <div class="text-sm font-semibold text-slate-200">
                  {{ app.company_name || 'Unknown Company' }}
                </div>
              </td>

              <!-- Platform -->
              <td class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-primary-900/30 text-primary-300 border border-primary-800">
                  <span class="mr-1">{{ getPlatformIcon(app.platform) }}</span>
                  {{ app.platform }}
                </span>
              </td>

              <!-- Match Score -->
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                  <span class="text-sm font-bold text-slate-100 mr-2">
                    {{ app.match_score }}%
                  </span>
                  <div class="w-16 h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      :style="{ width: app.match_score + '%' }"
                      :class="[
                        'h-full transition-all',
                        app.match_score >= 80 ? 'bg-success-500' : app.match_score >= 60 ? 'bg-warning-500' : 'bg-danger-500'
                      ]"
                    ></div>
                  </div>
                </div>
              </td>

              <!-- Status -->
              <td class="px-6 py-4 whitespace-nowrap">
                <span
                  :class="[
                    'px-3 py-1.5 inline-flex items-center text-xs leading-5 font-bold rounded-lg shadow-sm',
                    getStatusColor(app.status)
                  ]"
                >
                  {{ app.status || 'unknown' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Table Footer with Pagination -->
      <div class="px-6 py-4 bg-gradient-to-r from-slate-900 to-slate-800 border-t border-slate-800">
        <div class="flex flex-col md:flex-row items-center justify-between gap-4">
          <!-- Results Count -->
          <p class="text-sm text-slate-300 font-semibold flex items-center">
            <span class="inline-block w-2 h-2 bg-primary-500 rounded-full mr-2"></span>
            Showing
            {{ Math.min((historyStore.pagination.page - 1) * historyStore.pagination.pageSize + 1, historyStore.filteredApplications.length) }}-{{ Math.min(historyStore.pagination.page * historyStore.pagination.pageSize, historyStore.filteredApplications.length) }}
            of {{ historyStore.filteredApplications.length }} application(s)
          </p>

          <!-- Pagination Controls -->
          <div v-if="historyStore.totalPages > 1" class="flex items-center gap-2">
            <!-- Previous Button -->
            <button
              @click="previousPage"
              :disabled="historyStore.pagination.page === 1"
              class="px-4 py-2 bg-slate-700 text-slate-200 rounded-lg font-medium hover:bg-slate-600 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ← Previous
            </button>

            <!-- Page Numbers -->
            <div class="flex items-center gap-1">
              <button
                v-for="pageNum in pageNumbers"
                :key="pageNum"
                @click="typeof pageNum === 'number' ? goToPage(pageNum) : null"
                :disabled="pageNum === '...'"
                :class="[
                  'px-3 py-2 rounded-lg font-bold transition-all duration-200',
                  pageNum === historyStore.pagination.page
                    ? 'bg-primary-600 text-white shadow-lg'
                    : pageNum === '...'
                    ? 'text-slate-500 cursor-default'
                    : 'bg-slate-700 text-slate-200 hover:bg-slate-600'
                ]"
              >
                {{ pageNum }}
              </button>
            </div>

            <!-- Next Button -->
            <button
              @click="nextPage"
              :disabled="historyStore.pagination.page >= historyStore.totalPages"
              class="px-4 py-2 bg-slate-700 text-slate-200 rounded-lg font-medium hover:bg-slate-600 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next →
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Application Detail Modal -->
    <ApplicationDetailModal
      :application="selectedApplication"
      :isOpen="isModalOpen"
      @close="closeDetailModal"
    />
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
