/**
 * Application History Store - Pinia State Management
 *
 * Central state management for application history with filtering,
 * sorting, pagination, and statistics.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { historyAPI } from '../services/api'

export const useHistoryStore = defineStore('history', () => {
  // ==================== STATE ====================

  /**
   * Applications list
   */
  const applications = ref([])

  /**
   * Filters state
   */
  const filters = ref({
    search: '',
    platform: [], // ['linkedin', 'seek', 'indeed']
    dateRange: {
      start: null, // YYYY-MM-DD
      end: null, // YYYY-MM-DD
    },
    scoreRange: [0, 100], // [min, max]
    status: [], // ['completed', 'rejected', 'pending']
  })

  /**
   * Sort settings
   */
  const sort = ref({
    column: 'applied_date', // title, company, platform, applied_date, match_score, status
    order: 'desc', // asc, desc
  })

  /**
   * Pagination state
   */
  const pagination = ref({
    page: 1,
    pageSize: 25,
    total: 0,
  })

  /**
   * Loading state
   */
  const loading = ref(false)

  /**
   * Error state
   */
  const error = ref(null)

  // ==================== COMPUTED ====================

  /**
   * Client-side filtered applications (for search text filtering)
   */
  const filteredApplications = computed(() => {
    if (!filters.value.search) {
      return applications.value
    }

    const searchLower = filters.value.search.toLowerCase()
    return applications.value.filter(
      (app) =>
        app.job_title.toLowerCase().includes(searchLower) ||
        app.company_name.toLowerCase().includes(searchLower)
    )
  })

  /**
   * Statistics computed from current filtered applications
   */
  const statistics = computed(() => {
    if (!filteredApplications.value || filteredApplications.value.length === 0) {
      return {
        total: 0,
        thisWeek: 0,
        thisMonth: 0,
        avgMatchScore: 0,
        successRate: 0,
        platformDistribution: {},
      }
    }

    const now = new Date()
    const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
    const oneMonthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)

    let thisWeek = 0
    let thisMonth = 0
    let totalScore = 0
    let completedCount = 0
    const platformCounts = {}

    filteredApplications.value.forEach((app) => {
      const appliedDate = new Date(app.applied_date)

      // Count this week
      if (appliedDate >= oneWeekAgo) {
        thisWeek++
      }

      // Count this month
      if (appliedDate >= oneMonthAgo) {
        thisMonth++
      }

      // Sum scores
      totalScore += app.match_score || 0

      // Count completed
      if (app.status === 'completed') {
        completedCount++
      }

      // Platform distribution
      const platform = app.platform
      platformCounts[platform] = (platformCounts[platform] || 0) + 1
    })

    const total = filteredApplications.value.length
    const avgMatchScore = total > 0 ? Math.round(totalScore / total) : 0
    const successRate = total > 0 ? Math.round((completedCount / total) * 100) : 0

    return {
      total,
      thisWeek,
      thisMonth,
      avgMatchScore,
      successRate,
      platformDistribution: platformCounts,
    }
  })

  // ==================== ACTIONS ====================

  /**
   * Fetch application history from API
   * @param {Object} options - Optional overrides for pagination/filters
   */
  async function fetchHistory(options = {}) {
    loading.value = true
    error.value = null

    try {
      // Build query parameters
      const params = {
        // Pagination
        page: options.page || pagination.value.page,
        page_size: options.page_size || pagination.value.pageSize,

        // Sorting
        sort_by: options.sort_by || sort.value.column,
        sort_order: options.sort_order || sort.value.order,

        // Filters
        platform: options.platform || filters.value.platform,
        date_from: options.date_from || filters.value.dateRange.start,
        date_to: options.date_to || filters.value.dateRange.end,
        min_score: options.min_score || filters.value.scoreRange[0],
        max_score: options.max_score || filters.value.scoreRange[1],
        status: options.status || filters.value.status,
      }

      // Remove null/undefined/empty values
      Object.keys(params).forEach((key) => {
        if (
          params[key] === null ||
          params[key] === undefined ||
          params[key] === '' ||
          (Array.isArray(params[key]) && params[key].length === 0)
        ) {
          delete params[key]
        }
      })

      console.log('[HistoryStore] Fetching history with params:', params)

      const response = await historyAPI.list(params)

      applications.value = response.data.applications || []
      pagination.value.total = response.data.total || 0
      pagination.value.page = response.data.page || 1
      pagination.value.pageSize = response.data.page_size || 25

      console.log(
        `[HistoryStore] Fetched ${applications.value.length} applications (total: ${pagination.value.total})`
      )
    } catch (err) {
      console.error('[HistoryStore] Error fetching history:', err)
      error.value = err.message || 'Failed to fetch application history'
      applications.value = []
      pagination.value.total = 0
    } finally {
      loading.value = false
    }
  }

  /**
   * Update filters and refresh data
   * @param {Object} newFilters - Partial filter object to merge
   */
  async function updateFilters(newFilters) {
    // Merge new filters
    filters.value = {
      ...filters.value,
      ...newFilters,
    }

    // Reset to page 1 when filters change
    pagination.value.page = 1

    // Refresh data
    await fetchHistory()
  }

  /**
   * Update sort settings and refresh data
   * @param {string} column - Column to sort by
   * @param {string} order - Sort order (asc/desc)
   */
  async function updateSort(column, order = 'desc') {
    sort.value = { column, order }

    // Refresh data
    await fetchHistory()
  }

  /**
   * Update pagination and refresh data
   * @param {number} page - Page number
   * @param {number} pageSize - Optional page size
   */
  async function updatePagination(page, pageSize = null) {
    pagination.value.page = page

    if (pageSize !== null) {
      pagination.value.pageSize = pageSize
    }

    // Refresh data
    await fetchHistory()
  }

  /**
   * Clear all filters and refresh data
   */
  async function clearFilters() {
    filters.value = {
      search: '',
      platform: [],
      dateRange: {
        start: null,
        end: null,
      },
      scoreRange: [0, 100],
      status: [],
    }

    // Reset pagination to page 1
    pagination.value.page = 1

    // Refresh data
    await fetchHistory()
  }

  /**
   * Export applications to CSV
   * @param {Array} appsToExport - Applications to export (defaults to filteredApplications)
   * @returns {string} CSV content
   */
  function exportToCSV(appsToExport = null) {
    const apps = appsToExport || filteredApplications.value

    if (!apps || apps.length === 0) {
      console.warn('[HistoryStore] No applications to export')
      return ''
    }

    // CSV headers
    const headers = [
      'Job Title',
      'Company',
      'Platform',
      'Applied Date',
      'Match Score',
      'Status',
      'Location',
      'Salary (AUD/day)',
      'Job URL',
    ]

    // Helper to sanitize CSV fields (prevent CSV injection)
    const sanitizeField = (field) => {
      if (field === null || field === undefined) {
        return ''
      }

      const str = String(field)

      // Prevent CSV injection: fields starting with = + - @ are dangerous
      if (/^[=+\-@]/.test(str)) {
        return `'${str.replace(/"/g, '""')}'` // Prefix with quote
      }

      // Standard escaping
      return `"${str.replace(/"/g, '""')}"`
    }

    // Build CSV rows
    const rows = apps.map((app) => {
      return [
        sanitizeField(app.job_title),
        sanitizeField(app.company_name),
        sanitizeField(app.platform),
        sanitizeField(app.applied_date),
        sanitizeField(app.match_score),
        sanitizeField(app.status),
        sanitizeField(app.location),
        sanitizeField(app.salary_aud_per_day),
        sanitizeField(app.job_url),
      ].join(',')
    })

    // Combine headers and rows
    const csv = [headers.join(','), ...rows].join('\n')

    console.log(`[HistoryStore] Exported ${apps.length} applications to CSV`)

    return csv
  }

  /**
   * Download CSV file
   */
  function downloadCSV() {
    const csv = exportToCSV()

    if (!csv) {
      console.warn('[HistoryStore] No data to download')
      return
    }

    // Create blob and download
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)

    link.setAttribute('href', url)
    link.setAttribute(
      'download',
      `application-history-${new Date().toISOString().split('T')[0]}.csv`
    )
    link.style.visibility = 'hidden'

    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    console.log('[HistoryStore] CSV download initiated')
  }

  // ==================== INITIALIZATION ====================

  /**
   * Initialize store - fetch initial data
   */
  async function initialize() {
    console.log('[HistoryStore] Initializing history store')

    await fetchHistory()

    console.log('[HistoryStore] History store initialized')
  }

  // ==================== RETURN ====================

  return {
    // State
    applications,
    filters,
    sort,
    pagination,
    loading,
    error,

    // Computed
    filteredApplications,
    statistics,

    // Actions
    fetchHistory,
    updateFilters,
    updateSort,
    updatePagination,
    clearFilters,
    exportToCSV,
    downloadCSV,

    // Lifecycle
    initialize,
  }
})
