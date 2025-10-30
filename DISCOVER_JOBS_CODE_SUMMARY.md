# Discover Jobs Feature - Code Summary

## File Changes

### 1. API Client: `frontend/src/services/api.js`

```javascript
// Added new discoveryAPI section
export const discoveryAPI = {
  /**
   * Trigger job discovery from job boards
   * @returns {Promise} Discovery result with job counts per platform
   */
  discover: () => {
    return apiClient.post('/discover')
  },
}
```

### 2. Job Store: `frontend/src/stores/jobStore.js`

**Import Update:**
```javascript
import { jobsAPI, pipelineAPI, pendingAPI, discoveryAPI } from '../services/api'
```

**New State:**
```javascript
const loading = ref({
  jobs: false,
  pipeline: false,
  pending: false,
  discovering: false,  // NEW
})

const discoveryNotification = ref(null) // NEW: { type: 'success' | 'error', message: string }
```

**New Action:**
```javascript
async function discoverJobs() {
  loading.value.discovering = true
  error.value = null
  discoveryNotification.value = null

  try {
    console.log('[Store] Starting job discovery...')
    const response = await discoveryAPI.discover()

    // Parse response and build success message
    let message = 'Job discovery completed successfully!'

    if (response.data && response.data.pollers) {
      const counts = []
      let totalJobs = 0

      // Extract job counts from each poller
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

      if (totalJobs > 0) {
        message = `Discovered ${totalJobs} job${totalJobs === 1 ? '' : 's'}!`
        if (counts.length > 0) {
          message += ` (${counts.join(', ')})`
        }
      }
    }

    // Show success notification
    discoveryNotification.value = {
      type: 'success',
      message: message,
    }

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      discoveryNotification.value = null
    }, 5000)

    // Refresh all data
    await Promise.all([
      fetchJobs(),
      fetchPipeline(),
      fetchPending(),
    ])

    return response
  } catch (err) {
    console.error('[Store] Error during job discovery:', err)

    const errorMessage = err.response?.data?.message || err.message || 'Failed to discover jobs'

    // Show error notification
    discoveryNotification.value = {
      type: 'error',
      message: errorMessage,
    }

    error.value = errorMessage

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      discoveryNotification.value = null
    }, 5000)

    throw err
  } finally {
    loading.value.discovering = false
  }
}
```

**Export Update:**
```javascript
return {
  // State
  jobs,
  pipeline,
  pending,
  loading,
  error,
  connectionStatus,
  discoveryNotification, // NEW

  // Computed
  jobStats,

  // Actions
  fetchJobs,
  fetchPipeline,
  fetchPending,
  retryJob,
  approveJob,
  rejectJob,
  discoverJobs, // NEW

  // Lifecycle
  initialize,
  cleanup,
}
```

### 3. Dashboard Component: `frontend/src/components/Dashboard.vue`

**Script Section - Added Handler:**
```javascript
// Handle discover jobs button click
const handleDiscoverJobs = async () => {
  console.log('[Dashboard] Discover jobs clicked')
  try {
    await jobStore.discoverJobs()
  } catch (err) {
    console.error('[Dashboard] Discovery failed:', err)
    // Error is already handled in store
  }
}
```

**Template Section - Added Button:**
```vue
<!-- Right side actions -->
<div class="flex items-center space-x-4">
  <!-- Discover Jobs Button -->
  <button
    @click="handleDiscoverJobs"
    :disabled="jobStore.loading.discovering"
    class="group relative flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-primary-500 to-accent-500 rounded-xl font-semibold text-slate-50 shadow-lg transition-all duration-300 hover:shadow-xl hover:shadow-primary-500/50 hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-slate-950 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 disabled:hover:shadow-lg overflow-hidden"
  >
    <!-- Animated gradient background on hover -->
    <span class="absolute inset-0 bg-gradient-to-r from-primary-600 to-accent-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></span>

    <!-- Content -->
    <span class="relative z-10 text-xl transition-transform duration-300" :class="jobStore.loading.discovering ? 'animate-spin' : ''">
      {{ jobStore.loading.discovering ? '⏳' : '🔍' }}
    </span>
    <span class="relative z-10 whitespace-nowrap">
      {{ jobStore.loading.discovering ? 'Discovering...' : 'Discover Jobs' }}
    </span>
  </button>

  <!-- Connection Status Indicator -->
  <div class="flex items-center space-x-2 px-5 py-2.5 rounded-full...">
    <!-- existing connection status code -->
  </div>
</div>
```

**Template Section - Added Notification:**
```vue
<!-- Discovery Notification -->
<div
  v-if="jobStore.discoveryNotification"
  class="rounded-xl p-5 shadow-lg animate-slide-up backdrop-blur-sm border mt-6 transition-all duration-300"
  :class="{
    'bg-success-900/20 border-l-4 border-success-500 border-success-800': jobStore.discoveryNotification.type === 'success',
    'bg-danger-900/20 border-l-4 border-danger-500 border-danger-800': jobStore.discoveryNotification.type === 'error'
  }"
>
  <div class="flex items-start">
    <span class="mr-3 text-2xl" :class="{
      'text-success-400': jobStore.discoveryNotification.type === 'success',
      'text-danger-400': jobStore.discoveryNotification.type === 'error'
    }">
      {{ jobStore.discoveryNotification.type === 'success' ? '✅' : '❌' }}
    </span>
    <div class="flex-1">
      <p class="font-bold text-lg" :class="{
        'text-success-300': jobStore.discoveryNotification.type === 'success',
        'text-danger-300': jobStore.discoveryNotification.type === 'error'
      }">
        {{ jobStore.discoveryNotification.type === 'success' ? 'Success' : 'Error' }}
      </p>
      <p class="text-sm mt-1.5" :class="{
        'text-success-400': jobStore.discoveryNotification.type === 'success',
        'text-danger-400': jobStore.discoveryNotification.type === 'error'
      }">
        {{ jobStore.discoveryNotification.message }}
      </p>
    </div>
    <button
      @click="jobStore.discoveryNotification = null"
      class="transition-colors ml-4 focus:outline-none focus:ring-2"
      :class="{
        'text-success-400 hover:text-success-300 focus:ring-success-500': jobStore.discoveryNotification.type === 'success',
        'text-danger-400 hover:text-danger-300 focus:ring-danger-500': jobStore.discoveryNotification.type === 'error'
      }"
    >
      <span class="text-xl">×</span>
    </button>
  </div>
</div>
```

## Key Design Decisions

1. **Gradient Button**: Used primary-500 to accent-500 gradient to match the modern dark theme
2. **Icon Choice**: 🔍 for discovery (search metaphor), ⏳ for loading (time-based animation)
3. **Notification Auto-dismiss**: 5-second timeout to avoid cluttering the UI
4. **Error Handling**: Dual error state (store.error + discoveryNotification) for flexibility
5. **Data Refresh**: Refresh all three data sources (jobs, pipeline, pending) after discovery
6. **Loading Prevention**: Button disabled during discovery to prevent duplicate requests
7. **Accessibility**: Focus states, semantic HTML, disabled attribute, color + icon + text changes

## Visual States

### Default State
- Icon: 🔍
- Text: "Discover Jobs"
- Background: Gradient primary-500 to accent-500
- Cursor: pointer

### Hover State
- Background: Darker gradient overlay (primary-600 to accent-600)
- Transform: -translate-y-0.5 (slight lift)
- Shadow: Enhanced with glow (shadow-primary-500/50)

### Loading State
- Icon: ⏳ (spinning)
- Text: "Discovering..."
- Button: Disabled
- Opacity: 50%
- Cursor: not-allowed

### Focus State
- Ring: 2px primary-500
- Ring Offset: 2px slate-950

## Integration Points

1. **API Endpoint**: `/api/discover` (POST)
2. **WebSocket Event**: `job_discovery_complete`
3. **Store Actions**: `fetchJobs()`, `fetchPipeline()`, `fetchPending()`
4. **Notification System**: Reuses existing error display pattern
