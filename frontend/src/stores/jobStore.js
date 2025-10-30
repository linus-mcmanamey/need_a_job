/**
 * Job Store - Pinia State Management
 *
 * Central state management for jobs, pipeline metrics, and pending jobs.
 * Integrates with API client and WebSocket for real-time updates.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { jobsAPI, pipelineAPI, pendingAPI, discoveryAPI } from '../services/api'
import { wsClient } from '../services/websocket'

export const useJobStore = defineStore('jobs', () => {
  // ==================== STATE ====================

  /**
   * Jobs list
   */
  const jobs = ref([])

  /**
   * Pipeline metrics
   */
  const pipeline = ref({
    active_jobs: [],
    stage_counts: {},
    timestamp: null,
  })

  /**
   * Pending jobs requiring manual intervention
   */
  const pending = ref([])

  /**
   * Loading states
   */
  const loading = ref({
    jobs: false,
    pipeline: false,
    pending: false,
    discovering: false,
  })

  /**
   * Error state
   */
  const error = ref(null)

  /**
   * WebSocket connection status
   */
  const connectionStatus = ref('disconnected') // 'connected', 'connecting', 'disconnected', 'reconnecting'

  /**
   * Discovery notification state
   */
  const discoveryNotification = ref(null) // { type: 'success' | 'error', message: string }

  // ==================== COMPUTED ====================

  /**
   * Job statistics computed from jobs list
   */
  const jobStats = computed(() => {
    if (!jobs.value || jobs.value.length === 0) {
      return {
        total: 0,
        pending: 0,
        applied: 0,
        rejected: 0,
      }
    }

    const stats = {
      total: jobs.value.length,
      pending: 0,
      applied: 0,
      rejected: 0,
    }

    jobs.value.forEach((job) => {
      // Count by status
      if (job.status === 'pending' || job.status === 'failed') {
        stats.pending++
      } else if (job.status === 'completed') {
        stats.applied++
      } else if (job.status === 'rejected') {
        stats.rejected++
      }
    })

    return stats
  })

  // ==================== ACTIONS ====================

  /**
   * Fetch jobs from API
   * @param {Object} params - Query parameters
   */
  async function fetchJobs(params = {}) {
    loading.value.jobs = true
    error.value = null

    try {
      const response = await jobsAPI.list(params)
      jobs.value = response.data.jobs || []
      console.log(`[Store] Fetched ${jobs.value.length} jobs`)
    } catch (err) {
      console.error('[Store] Error fetching jobs:', err)
      error.value = err.message || 'Failed to fetch jobs'
      jobs.value = []
    } finally {
      loading.value.jobs = false
    }
  }

  /**
   * Fetch pipeline metrics from API
   */
  async function fetchPipeline() {
    loading.value.pipeline = true
    error.value = null

    try {
      const response = await pipelineAPI.status()
      pipeline.value = response.data
      console.log('[Store] Fetched pipeline metrics')
    } catch (err) {
      console.error('[Store] Error fetching pipeline:', err)
      error.value = err.message || 'Failed to fetch pipeline'
      pipeline.value = { active_jobs: [], stage_counts: {}, timestamp: null }
    } finally {
      loading.value.pipeline = false
    }
  }

  /**
   * Fetch pending jobs from API
   * @param {number} limit - Maximum number of jobs to fetch
   */
  async function fetchPending(limit = 20) {
    loading.value.pending = true
    error.value = null

    try {
      const response = await pendingAPI.list(limit)
      pending.value = response.data.pending_jobs || []
      console.log(`[Store] Fetched ${pending.value.length} pending jobs`)
    } catch (err) {
      console.error('[Store] Error fetching pending jobs:', err)
      error.value = err.message || 'Failed to fetch pending jobs'
      pending.value = []
    } finally {
      loading.value.pending = false
    }
  }

  /**
   * Retry a job
   * @param {string} jobId - Job ID to retry
   */
  async function retryJob(jobId) {
    try {
      await jobsAPI.retry(jobId)
      console.log(`[Store] Job ${jobId} retry requested`)

      // Refresh jobs list to reflect changes
      await fetchJobs()
    } catch (err) {
      console.error(`[Store] Error retrying job ${jobId}:`, err)
      error.value = err.message || 'Failed to retry job'
      throw err
    }
  }

  /**
   * Approve a pending job
   * @param {string} jobId - Job ID to approve
   */
  async function approveJob(jobId) {
    try {
      await pendingAPI.approve(jobId)
      console.log(`[Store] Job ${jobId} approved`)

      // Refresh pending jobs list
      await fetchPending()
    } catch (err) {
      console.error(`[Store] Error approving job ${jobId}:`, err)
      error.value = err.message || 'Failed to approve job'
      throw err
    }
  }

  /**
   * Reject a pending job
   * @param {string} jobId - Job ID to reject
   * @param {string} reason - Rejection reason
   */
  async function rejectJob(jobId, reason = 'User rejected') {
    try {
      await pendingAPI.reject(jobId, reason)
      console.log(`[Store] Job ${jobId} rejected: ${reason}`)

      // Refresh pending jobs list
      await fetchPending()
    } catch (err) {
      console.error(`[Store] Error rejecting job ${jobId}:`, err)
      error.value = err.message || 'Failed to reject job'
      throw err
    }
  }

  /**
   * Trigger job discovery from job boards
   * @returns {Promise} Discovery result with job counts
   */
  async function discoverJobs() {
    loading.value.discovering = true
    error.value = null
    discoveryNotification.value = null

    try {
      console.log('[Store] Starting job discovery...')
      const response = await discoveryAPI.discover()

      // Build success message from response data
      let message = 'Job discovery completed successfully!'

      if (response.data && response.data.pollers) {
        const counts = []
        let totalJobs = 0

        // Extract job counts from pollers
        const pollers = response.data.pollers

        if (pollers.seek && pollers.seek.jobs_added !== undefined) {
          const seekCount = pollers.seek.jobs_added
          counts.push(`${seekCount} from SEEK`)
          totalJobs += seekCount
        }

        if (pollers.indeed && pollers.indeed.jobs_added !== undefined) {
          const indeedCount = pollers.indeed.jobs_added
          counts.push(`${indeedCount} from Indeed`)
          totalJobs += indeedCount
        }

        if (pollers.linkedin && pollers.linkedin.jobs_added !== undefined) {
          const linkedInCount = pollers.linkedin.jobs_added
          counts.push(`${linkedInCount} from LinkedIn`)
          totalJobs += linkedInCount
        }

        // Build message
        if (totalJobs > 0) {
          message = `Discovered ${totalJobs} job${totalJobs === 1 ? '' : 's'}!`
          if (counts.length > 0) {
            message += ` (${counts.join(', ')})`
          }
        } else if (counts.length > 0) {
          message = `Discovery completed: ${counts.join(', ')}`
        }
      }

      discoveryNotification.value = {
        type: 'success',
        message: message,
      }

      console.log('[Store] Job discovery completed:', message)

      // Auto-dismiss notification after 5 seconds
      setTimeout(() => {
        discoveryNotification.value = null
      }, 5000)

      // Refresh jobs and pipeline data
      await Promise.all([
        fetchJobs(),
        fetchPipeline(),
        fetchPending(),
      ])

      return response
    } catch (err) {
      console.error('[Store] Error during job discovery:', err)

      const errorMessage = err.response?.data?.message || err.message || 'Failed to discover jobs'

      discoveryNotification.value = {
        type: 'error',
        message: errorMessage,
      }

      error.value = errorMessage

      // Auto-dismiss error notification after 5 seconds
      setTimeout(() => {
        discoveryNotification.value = null
      }, 5000)

      throw err
    } finally {
      loading.value.discovering = false
    }
  }

  // ==================== WEBSOCKET HANDLERS ====================

  /**
   * Handle job_update WebSocket event
   * @param {Object} message - WebSocket message
   */
  function handleJobUpdate(message) {
    console.log('[Store] WebSocket job_update:', message)

    const { job_id, status, action } = message

    // Update job in jobs list if present
    const jobIndex = jobs.value.findIndex((j) => j.job_id === job_id)
    if (jobIndex !== -1) {
      jobs.value[jobIndex].status = status
    }

    // If job was approved/rejected, refresh pending list
    if (action === 'approve' || action === 'reject') {
      fetchPending()
    }

    // Refresh jobs list to get latest data
    fetchJobs()
  }

  /**
   * Handle job_retry WebSocket event
   * @param {Object} message - WebSocket message
   */
  function handleJobRetry(message) {
    console.log('[Store] WebSocket job_retry:', message)

    // Refresh jobs list to reflect retry
    fetchJobs()
  }

  /**
   * Handle pipeline_update WebSocket event
   * @param {Object} message - WebSocket message
   */
  function handlePipelineUpdate(message) {
    console.log('[Store] WebSocket pipeline_update:', message)

    // Refresh pipeline metrics
    fetchPipeline()
  }

  /**
   * Handle job_discovery_complete WebSocket event
   * @param {Object} message - WebSocket message
   */
  function handleJobDiscoveryComplete(message) {
    console.log('[Store] WebSocket job_discovery_complete:', message)

    // Refresh jobs list as new jobs were discovered
    fetchJobs()
  }

  /**
   * Setup WebSocket event listeners
   */
  function setupWebSocketListeners() {
    console.log('[Store] Setting up WebSocket listeners')

    wsClient.on('job_update', handleJobUpdate)
    wsClient.on('job_retry', handleJobRetry)
    wsClient.on('pipeline_update', handlePipelineUpdate)
    wsClient.on('job_discovery_complete', handleJobDiscoveryComplete)
  }

  /**
   * Cleanup WebSocket event listeners
   */
  function cleanupWebSocketListeners() {
    console.log('[Store] Cleaning up WebSocket listeners')

    wsClient.off('job_update', handleJobUpdate)
    wsClient.off('job_retry', handleJobRetry)
    wsClient.off('pipeline_update', handlePipelineUpdate)
    wsClient.off('job_discovery_complete', handleJobDiscoveryComplete)
  }

  // ==================== INITIALIZATION ====================

  /**
   * Initialize store - fetch initial data and setup WebSocket
   */
  async function initialize() {
    console.log('[Store] Initializing job store')

    // Setup WebSocket listeners first
    setupWebSocketListeners()

    // Connect to WebSocket
    connectionStatus.value = 'connecting'
    try {
      await wsClient.connect()
      connectionStatus.value = 'connected'
    } catch (err) {
      console.error('[Store] WebSocket connection failed:', err)
      connectionStatus.value = 'disconnected'
      // Continue anyway - polling will work
    }

    // Monitor connection status
    setInterval(() => {
      if (wsClient.isConnected()) {
        if (connectionStatus.value !== 'connected') {
          connectionStatus.value = 'connected'
        }
      } else {
        if (connectionStatus.value === 'connected') {
          connectionStatus.value = 'reconnecting'
        }
      }
    }, 2000)

    // Fetch initial data
    await Promise.all([
      fetchJobs(),
      fetchPipeline(),
      fetchPending(),
    ])

    console.log('[Store] Job store initialized')
  }

  /**
   * Cleanup store - disconnect WebSocket and clear listeners
   */
  function cleanup() {
    console.log('[Store] Cleaning up job store')

    cleanupWebSocketListeners()
    wsClient.disconnect()
  }

  // ==================== RETURN ====================

  return {
    // State
    jobs,
    pipeline,
    pending,
    loading,
    error,
    connectionStatus,
    discoveryNotification,

    // Computed
    jobStats,

    // Actions
    fetchJobs,
    fetchPipeline,
    fetchPending,
    retryJob,
    approveJob,
    rejectJob,
    discoverJobs,

    // Lifecycle
    initialize,
    cleanup,
  }
})
