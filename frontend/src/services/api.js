/**
 * HTTP API Client for Job Application Automation System
 *
 * Provides axios-based HTTP client with organized API endpoint methods.
 */

import axios from 'axios'

// Get API base URL from environment variables
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for logging (development only)
apiClient.interceptors.request.use(
  (config) => {
    if (import.meta.env.DEV) {
      console.log(`[API] ${config.method.toUpperCase()} ${config.url}`)
    }
    return config
  },
  (error) => {
    console.error('[API] Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response) {
      // Server responded with error status
      console.error('[API] Response error:', error.response.status, error.response.data)
    } else if (error.request) {
      // Request made but no response received
      console.error('[API] No response received:', error.request)
    } else {
      // Error setting up request
      console.error('[API] Request setup error:', error.message)
    }
    return Promise.reject(error)
  }
)

/**
 * Jobs API endpoints
 */
export const jobsAPI = {
  /**
   * List all jobs with optional filtering
   * @param {Object} params - Query parameters (platform, limit, offset)
   * @returns {Promise} Jobs list with pagination
   */
  list: (params = {}) => {
    return apiClient.get('/jobs', { params })
  },

  /**
   * Get a specific job by ID
   * @param {string} jobId - Job ID
   * @returns {Promise} Job details
   */
  get: (jobId) => {
    return apiClient.get(`/jobs/${jobId}`)
  },

  /**
   * Retry a failed or pending job
   * @param {string} jobId - Job ID
   * @returns {Promise} Retry result
   */
  retry: (jobId) => {
    return apiClient.post(`/jobs/${jobId}/retry`)
  },
}

/**
 * Pipeline API endpoints
 */
export const pipelineAPI = {
  /**
   * Get current pipeline status and metrics
   * @returns {Promise} Pipeline metrics
   */
  status: () => {
    return apiClient.get('/pipeline')
  },
}

/**
 * Pending Jobs API endpoints
 */
export const pendingAPI = {
  /**
   * List jobs requiring manual intervention
   * @param {number} limit - Maximum number of jobs to return
   * @returns {Promise} Pending jobs list
   */
  list: (limit = 20) => {
    return apiClient.get('/pending', { params: { limit } })
  },

  /**
   * Approve a pending job for submission
   * @param {string} jobId - Job ID
   * @returns {Promise} Approve result
   */
  approve: (jobId) => {
    return apiClient.post(`/pending/${jobId}/approve`)
  },

  /**
   * Reject a pending job
   * @param {string} jobId - Job ID
   * @param {string} reason - Optional rejection reason
   * @returns {Promise} Reject result
   */
  reject: (jobId, reason = 'User rejected') => {
    return apiClient.post(`/pending/${jobId}/reject`, null, {
      params: { reason }
    })
  },
}

/**
 * Discovery API endpoints
 */
export const discoveryAPI = {
  /**
   * Trigger job discovery from job boards
   * @returns {Promise} Discovery result with job counts per platform
   */
  discover: () => {
    return apiClient.post('/discover')
  },
}

// Export axios instance for direct use if needed
export default apiClient
