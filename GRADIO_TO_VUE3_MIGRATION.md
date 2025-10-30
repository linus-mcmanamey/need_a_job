# Gradio to Vue 3 + FastAPI Frontend Migration Guide

## Overview

Replace the Gradio UI (`app/ui/gradio_app.py`) with a modern Vue 3 frontend while leveraging the existing FastAPI backend and Redis job queue. This decouples the UI from business logic and provides better real-time capabilities.

## Architecture

```
need_a_job/
├── app/
│   ├── main.py                 # FastAPI (unchanged)
│   ├── agents/                 # (unchanged)
│   ├── services/               # (unchanged)
│   ├── repositories/           # (unchanged)
│   ├── models/                 # (unchanged - Pydantic V2)
│   └── ui/
│       ├── gradio_app.py       # DELETE THIS
│       └── websocket.py        # NEW: WebSocket connection manager
├── frontend/                   # NEW: Vue 3 project
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.vue
│   │   │   ├── JobTable.vue
│   │   │   ├── PipelineView.vue
│   │   │   └── SettingsPanel.vue
│   │   ├── services/
│   │   │   ├── api.js          # HTTP client for FastAPI
│   │   │   └── websocket.js    # WebSocket client
│   │   ├── stores/
│   │   │   └── jobStore.js     # Pinia state management
│   │   ├── App.vue
│   │   └── main.js
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
├── docker-compose.yml          # UPDATED
└── Dockerfile                  # UPDATED
```

## Step 1: Add WebSocket Support to FastAPI

**File: `app/ui/websocket.py`** (NEW)

```python
from fastapi import WebSocket
from typing import Set
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()
```

## Step 2: Update FastAPI to Include WebSocket Endpoints

**File: `app/main.py`** (ADDITIONS)

```python
from fastapi import WebSocket, WebSocketDisconnect
from app.ui.websocket import manager
from contextlib import asynccontextmanager

# Add WebSocket route
@app.websocket("/ws/status")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo or handle client messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Update pipeline/job endpoints to broadcast status changes
# Example modification to existing endpoint:
@app.post("/api/jobs/{id}/retry")
async def retry_job(id: str):
    result = retry_job_logic(id)
    await manager.broadcast({
        "type": "job_retry",
        "job_id": id,
        "status": result.status
    })
    return result
```

**Update existing endpoints to emit WebSocket events when state changes:**
- Job discovery completion → broadcast job list
- Pipeline status update → broadcast pipeline metrics
- Application submission → broadcast application status

## Step 3: Create Vue 3 Frontend Project

**Terminal commands:**

```bash
# Navigate to project root
cd need_a_job

# Create Vue 3 project with Vite
npm create vite@latest frontend -- --template vue

cd frontend

# Install dependencies
npm install

# Install additional packages
npm install axios pinia vue-router
npm install -D tailwindcss postcss autoprefixer

# Initialize Tailwind (optional but recommended)
npx tailwindcss init -p
```

## Step 4: Frontend Project Structure

### `frontend/src/main.js`

```javascript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.mount('#app')
```

### `frontend/src/services/api.js`

```javascript
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const jobsAPI = {
  list: () => api.get('/jobs'),
  get: (id) => api.get(`/jobs/${id}`),
  retry: (id) => api.post(`/jobs/${id}/retry`),
}

export const pipelineAPI = {
  status: () => api.get('/pipeline'),
}

export const pendingAPI = {
  list: () => api.get('/pending'),
  approve: (id) => api.post(`/pending/${id}/approve`),
  reject: (id) => api.post(`/pending/${id}/reject`),
}

export default api
```

### `frontend/src/services/websocket.js`

```javascript
export class WebSocketClient {
  constructor(url) {
    this.url = url
    this.ws = null
    this.handlers = {}
  }

  connect() {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url)
        this.ws.onopen = () => resolve()
        this.ws.onmessage = (event) => this.handleMessage(event)
        this.ws.onerror = () => reject()
        this.ws.onclose = () => this.reconnect()
      } catch (e) {
        reject(e)
      }
    })
  }

  handleMessage(event) {
    const message = JSON.parse(event.data)
    const handler = this.handlers[message.type]
    if (handler) handler(message)
  }

  on(type, handler) {
    this.handlers[type] = handler
  }

  send(message) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    }
  }

  reconnect() {
    setTimeout(() => this.connect(), 3000)
  }

  close() {
    this.ws?.close()
  }
}

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/status'
export const wsClient = new WebSocketClient(WS_URL)
```

### `frontend/src/stores/jobStore.js`

```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { jobsAPI, pipelineAPI, pendingAPI } from '../services/api'
import { wsClient } from '../services/websocket'

export const useJobStore = defineStore('jobs', () => {
  const jobs = ref([])
  const pipeline = ref(null)
  const pending = ref([])
  const loading = ref(false)
  const error = ref(null)

  const jobStats = computed(() => ({
    total: jobs.value.length,
    pending: jobs.value.filter(j => j.status === 'pending').length,
    applied: jobs.value.filter(j => j.status === 'applied').length,
    rejected: jobs.value.filter(j => j.status === 'rejected').length,
  }))

  const fetchJobs = async () => {
    loading.value = true
    try {
      const response = await jobsAPI.list()
      jobs.value = response.data
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  const fetchPipeline = async () => {
    try {
      const response = await pipelineAPI.status()
      pipeline.value = response.data
    } catch (e) {
      error.value = e.message
    }
  }

  const fetchPending = async () => {
    try {
      const response = await pendingAPI.list()
      pending.value = response.data
    } catch (e) {
      error.value = e.message
    }
  }

  const retryJob = async (jobId) => {
    try {
      await jobsAPI.retry(jobId)
      await fetchJobs()
    } catch (e) {
      error.value = e.message
    }
  }

  const approveJob = async (jobId) => {
    try {
      await pendingAPI.approve(jobId)
      await fetchPending()
    } catch (e) {
      error.value = e.message
    }
  }

  const rejectJob = async (jobId) => {
    try {
      await pendingAPI.reject(jobId)
      await fetchPending()
    } catch (e) {
      error.value = e.message
    }
  }

  // WebSocket handlers
  const setupWebSocketHandlers = () => {
    wsClient.on('job_update', (data) => {
      const idx = jobs.value.findIndex(j => j.id === data.job_id)
      if (idx >= 0) {
        jobs.value[idx].status = data.status
      }
    })

    wsClient.on('pipeline_update', (data) => {
      pipeline.value = data
    })

    wsClient.on('job_discovery_complete', () => {
      fetchJobs()
    })
  }

  const initialize = async () => {
    await wsClient.connect()
    setupWebSocketHandlers()
    await Promise.all([fetchJobs(), fetchPipeline(), fetchPending()])
  }

  return {
    jobs,
    pipeline,
    pending,
    loading,
    error,
    jobStats,
    fetchJobs,
    fetchPipeline,
    fetchPending,
    retryJob,
    approveJob,
    rejectJob,
    initialize,
  }
})
```

### `frontend/src/components/Dashboard.vue`

```vue
<template>
  <div class="p-8 bg-gray-50 min-h-screen">
    <h1 class="text-3xl font-bold mb-8">Job Application Dashboard</h1>

    <!-- Stats -->
    <div class="grid grid-cols-4 gap-4 mb-8">
      <div class="bg-white p-6 rounded-lg shadow">
        <p class="text-gray-600">Total Jobs</p>
        <p class="text-3xl font-bold">{{ jobStore.jobStats.total }}</p>
      </div>
      <div class="bg-white p-6 rounded-lg shadow">
        <p class="text-gray-600">Pending</p>
        <p class="text-3xl font-bold text-yellow-600">{{ jobStore.jobStats.pending }}</p>
      </div>
      <div class="bg-white p-6 rounded-lg shadow">
        <p class="text-gray-600">Applied</p>
        <p class="text-3xl font-bold text-green-600">{{ jobStore.jobStats.applied }}</p>
      </div>
      <div class="bg-white p-6 rounded-lg shadow">
        <p class="text-gray-600">Rejected</p>
        <p class="text-3xl font-bold text-red-600">{{ jobStore.jobStats.rejected }}</p>
      </div>
    </div>

    <!-- Tabs -->
    <div class="flex gap-2 mb-4 border-b">
      <button
        v-for="tab in ['jobs', 'pipeline', 'pending']"
        :key="tab"
        @click="activeTab = tab"
        :class="{
          'border-b-2 border-blue-600 font-bold': activeTab === tab,
          'text-gray-600': activeTab !== tab,
        }"
        class="px-4 py-2"
      >
        {{ tab.charAt(0).toUpperCase() + tab.slice(1) }}
      </button>
    </div>

    <!-- Content -->
    <div class="bg-white rounded-lg shadow p-6">
      <JobTable v-if="activeTab === 'jobs'" :jobs="jobStore.jobs" />
      <PipelineView v-if="activeTab === 'pipeline'" :pipeline="jobStore.pipeline" />
      <PendingJobs v-if="activeTab === 'pending'" :pending="jobStore.pending" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useJobStore } from '../stores/jobStore'
import JobTable from './JobTable.vue'
import PipelineView from './PipelineView.vue'
import PendingJobs from './PendingJobs.vue'

const jobStore = useJobStore()
const activeTab = ref('jobs')

onMounted(async () => {
  await jobStore.initialize()
})
</script>
```

### `frontend/src/components/JobTable.vue`

```vue
<template>
  <div class="overflow-x-auto">
    <table class="w-full text-sm">
      <thead class="bg-gray-100">
        <tr>
          <th class="px-4 py-2 text-left">Title</th>
          <th class="px-4 py-2 text-left">Company</th>
          <th class="px-4 py-2 text-left">Status</th>
          <th class="px-4 py-2 text-left">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="job in jobs" :key="job.id" class="border-b hover:bg-gray-50">
          <td class="px-4 py-2">{{ job.title }}</td>
          <td class="px-4 py-2">{{ job.company }}</td>
          <td class="px-4 py-2">
            <span :class="{
              'bg-yellow-100 text-yellow-800': job.status === 'pending',
              'bg-green-100 text-green-800': job.status === 'applied',
              'bg-red-100 text-red-800': job.status === 'rejected',
            }" class="px-2 py-1 rounded text-xs font-semibold">
              {{ job.status }}
            </span>
          </td>
          <td class="px-4 py-2">
            <button
              v-if="job.status === 'rejected'"
              @click="jobStore.retryJob(job.id)"
              class="text-blue-600 hover:underline text-sm"
            >
              Retry
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { useJobStore } from '../stores/jobStore'

defineProps({
  jobs: Array,
})

const jobStore = useJobStore()
</script>
```

### `frontend/src/components/PipelineView.vue`

```vue
<template>
  <div v-if="pipeline" class="space-y-4">
    <div class="grid grid-cols-3 gap-4">
      <div class="bg-blue-50 p-4 rounded">
        <p class="text-sm text-gray-600">Discovery Queue</p>
        <p class="text-2xl font-bold">{{ pipeline.discovery_queue }}</p>
      </div>
      <div class="bg-purple-50 p-4 rounded">
        <p class="text-sm text-gray-600">Active Jobs</p>
        <p class="text-2xl font-bold">{{ pipeline.active_processing }}</p>
      </div>
      <div class="bg-green-50 p-4 rounded">
        <p class="text-sm text-gray-600">Completed</p>
        <p class="text-2xl font-bold">{{ pipeline.completed }}</p>
      </div>
    </div>
  </div>
  <div v-else class="text-gray-500">Loading pipeline status...</div>
</template>

<script setup>
defineProps({
  pipeline: Object,
})
</script>
```

### `frontend/src/components/PendingJobs.vue`

```vue
<template>
  <div v-if="pending.length" class="space-y-4">
    <div v-for="job in pending" :key="job.id" class="border p-4 rounded">
      <div class="flex justify-between items-start mb-4">
        <div>
          <h3 class="font-bold">{{ job.title }}</h3>
          <p class="text-sm text-gray-600">{{ job.company }}</p>
        </div>
        <div class="space-x-2">
          <button
            @click="jobStore.approveJob(job.id)"
            class="bg-green-600 text-white px-4 py-2 rounded text-sm hover:bg-green-700"
          >
            Approve
          </button>
          <button
            @click="jobStore.rejectJob(job.id)"
            class="bg-red-600 text-white px-4 py-2 rounded text-sm hover:bg-red-700"
          >
            Reject
          </button>
        </div>
      </div>
      <p class="text-sm text-gray-700">{{ job.description }}</p>
    </div>
  </div>
  <div v-else class="text-gray-500 text-center py-8">No pending jobs for review</div>
</template>

<script setup>
import { useJobStore } from '../stores/jobStore'

defineProps({
  pending: Array,
})

const jobStore = useJobStore()
</script>
```

## Step 5: Environment Files

**`frontend/.env.example`**

```
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws/status
```

**`frontend/.env.development`**

```
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws/status
```

**`frontend/.env.production`**

```
VITE_API_URL=https://api.yourdomain.com/api
VITE_WS_URL=wss://api.yourdomain.com/ws/status
```

## Step 6: Update Docker Compose

**`docker-compose.yml`** (ADDITIONS/MODIFICATIONS)

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - PYTHONUNBUFFERED=1
    depends_on:
      - redis
    volumes:
      - ./app:/app/app
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

  worker:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379
      - PYTHONUNBUFFERED=1
    depends_on:
      - redis
    volumes:
      - ./app:/app/app
    command: rq worker discovery_queue pipeline_queue --url redis://redis:6379
    deploy:
      replicas: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev

volumes:
  redis_data:
```

**`frontend/Dockerfile`** (NEW)

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev"]
```

**`frontend/package.json`** (key scripts)

```json
{
  "scripts": {
    "dev": "vite --host 0.0.0.0",
    "build": "vite build",
    "preview": "vite preview"
  }
}
```

## Step 7: Update Dockerfile for Backend

**`Dockerfile`** (MODIFICATION - remove Gradio)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
RUN pip install poetry && poetry install --no-dev

COPY app ./app
COPY config ./config

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Migration Checklist

- [ ] Add `app/ui/websocket.py` with ConnectionManager
- [ ] Update `app/main.py` with WebSocket endpoint and broadcast logic
- [ ] Create `frontend/` Vue 3 project structure
- [ ] Implement all Vue components (Dashboard, JobTable, PipelineView, PendingJobs)
- [ ] Implement Pinia store with API and WebSocket integration
- [ ] Create API and WebSocket service clients
- [ ] Update environment files
- [ ] Update `docker-compose.yml` with frontend service
- [ ] Update backend `Dockerfile` (remove Gradio)
- [ ] Create `frontend/Dockerfile`
- [ ] Delete `app/ui/gradio_app.py`
- [ ] Remove Gradio from `pyproject.toml`/`requirements.txt`
- [ ] Test locally: `docker-compose up`
- [ ] Access UI at `http://localhost:5173`
- [ ] Verify API at `http://localhost:8000/api/docs`

## Testing Checklist

- [ ] Dashboard loads without errors
- [ ] Job stats display correctly
- [ ] Tab switching works (jobs/pipeline/pending)
- [ ] WebSocket connection establishes
- [ ] Real-time job status updates appear
- [ ] Retry button sends request to FastAPI
- [ ] Approve/reject buttons work
- [ ] Responsive design on mobile

## Deployment Notes

**Local:**
```bash
docker-compose up
# Frontend: http://localhost:5173
# API: http://localhost:8000
```

**Production:**
- Build frontend: `npm run build` → outputs to `dist/`
- Serve frontend via nginx or include in backend container
- Update env vars for production domain
- Use `wss://` for WebSocket (require HTTPS)

## Notes for Agent

- This preserves all FastAPI business logic unchanged
- Pydantic V2 models work transparently with JSON serialization
- Redis + RQ workers continue operating independently
- WebSocket adds real-time capability without polling
- Vue 3 + Pinia is modern, maintainable, and performant
- Easy to extend with additional views/features
- Can deploy frontend and backend independently if needed
