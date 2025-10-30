# Discover Jobs Feature Implementation

## Overview
Added a "Discover Jobs" button to the Dashboard component that triggers job discovery from configured job boards (SEEK, Indeed, LinkedIn).

## Implementation Summary

### 1. API Client (`frontend/src/services/api.js`)
**Added:**
- `discoveryAPI.discover()` - POST endpoint to `/api/discover`

### 2. Job Store (`frontend/src/stores/jobStore.js`)
**Added State:**
- `loading.discovering` - Boolean flag for discovery loading state
- `discoveryNotification` - Object containing notification data `{ type: 'success' | 'error', message: string }`

**Added Actions:**
- `discoverJobs()` - Main action that:
  - Calls the discovery API endpoint
  - Handles loading states
  - Parses poller results from backend
  - Shows success/error notifications
  - Auto-dismisses notifications after 5 seconds
  - Refreshes jobs, pipeline, and pending data after completion

### 3. Dashboard Component (`frontend/src/components/Dashboard.vue`)
**Added UI Elements:**
- **Discover Jobs Button** (lines 85-100):
  - Located in header next to connection status
  - Gradient button style (primary-500 to accent-500)
  - Icon: 🔍 (magnifying glass) - changes to ⏳ (hourglass) with spin animation when discovering
  - Text: "Discover Jobs" - changes to "Discovering..." when active
  - Disabled state during discovery
  - Hover effects with shadow and transform
  - Focus states with ring

- **Discovery Notification** (lines 280-321):
  - Success notification (green) with job counts from each platform
  - Error notification (red) with error details
  - Dismissible via close button
  - Auto-dismisses after 5 seconds

**Added Logic:**
- `handleDiscoverJobs()` - Click handler that calls `jobStore.discoverJobs()`

## Features

### Button Design
- **Gradient Background**: primary-500 to accent-500
- **Hover Effects**:
  - Darker gradient overlay
  - Shadow glow (shadow-primary-500/50)
  - Slight upward transform (-translate-y-0.5)
- **Focus States**: Ring with offset
- **Disabled States**:
  - Reduced opacity (50%)
  - No pointer cursor
  - No transform effects

### Loading State
- Button disabled during discovery
- Icon changes to spinning hourglass (⏳)
- Text changes to "Discovering..."

### Success Feedback
- Green notification banner
- Example message: "Discovered 45 jobs! (32 from SEEK, 13 from Indeed)"
- Includes job counts per platform
- Auto-dismisses after 5 seconds

### Error Handling
- Red notification banner
- Shows error message from API
- Also sets store error state
- Auto-dismisses after 5 seconds
- User can manually dismiss

### Data Refresh
After successful discovery:
- Refreshes jobs list
- Refreshes pipeline metrics
- Refreshes pending jobs list

### WebSocket Integration
- Backend broadcasts `job_discovery_complete` event
- Store already has listener configured (line 261)
- Automatically refreshes jobs when WebSocket event received

## Backend Integration

### Endpoint
```
POST /api/discover
```

### Response Format
```json
{
  "status": "completed",
  "timestamp": "2025-10-30T12:34:56.789",
  "pollers": {
    "seek": {
      "jobs_added": 32,
      "jobs_updated": 5,
      "duplicates_found": 2
    },
    "indeed": {
      "jobs_added": 13,
      "jobs_updated": 1,
      "duplicates_found": 0
    }
  }
}
```

### WebSocket Event
```json
{
  "type": "job_discovery_complete",
  "results": { /* same as response above */ }
}
```

## Files Modified

1. `/frontend/src/services/api.js` - Added discoveryAPI
2. `/frontend/src/stores/jobStore.js` - Added discovery action and state
3. `/frontend/src/components/Dashboard.vue` - Added button and notifications

## Usage

### User Flow
1. User clicks "Discover Jobs" button in Dashboard header
2. Button shows loading state ("Discovering..." with spinning icon)
3. API call triggers backend pollers (SEEK, Indeed, etc.)
4. Success notification appears with job counts
5. Jobs list automatically refreshes
6. Notification auto-dismisses after 5 seconds

### Developer Notes
- Discovery respects search configuration (search.yaml)
- Only enabled pollers will run
- Timeout set to 10 seconds in API client
- All errors are caught and displayed to user
- Loading state prevents double-clicks

## Accessibility
- Button has focus ring states
- Semantic HTML button element
- Loading state communicated via disabled attribute
- Color is not the only indicator (icons and text also change)
- Keyboard navigation supported

## Performance
- Async/await pattern for clean code
- Parallel data refresh after discovery
- Non-blocking UI (discovery runs in background)
- Auto-dismissing notifications reduce visual clutter

## Testing Checklist
- [ ] Button appears in Dashboard header
- [ ] Button is positioned correctly next to connection status
- [ ] Click triggers discovery API call
- [ ] Loading state shows correctly
- [ ] Button is disabled during discovery
- [ ] Success notification shows with job counts
- [ ] Error notification shows on API failure
- [ ] Notifications auto-dismiss after 5 seconds
- [ ] Jobs list refreshes after discovery
- [ ] Pipeline metrics update after discovery
- [ ] Pending jobs update after discovery
- [ ] WebSocket events trigger data refresh
- [ ] Hover effects work correctly
- [ ] Focus states visible for keyboard navigation
