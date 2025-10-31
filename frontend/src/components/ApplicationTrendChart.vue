<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Filler
} from 'chart.js'

// Register Chart.js components
ChartJS.register(
  Title,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Filler
)

// Props
const props = defineProps({
  applications: {
    type: Array,
    required: true,
    default: () => []
  }
})

/**
 * Get week label from date
 */
function getWeekLabel(date) {
  const month = date.toLocaleDateString('en-US', { month: 'short' })
  const day = date.getDate()
  return `${month} ${day}`
}

/**
 * Get start of week (Sunday)
 */
function getWeekStart(date) {
  const d = new Date(date)
  const day = d.getDay()
  const diff = d.getDate() - day
  d.setDate(diff)
  d.setHours(0, 0, 0, 0)
  return d
}

/**
 * Chart data computed from applications (last 12 weeks)
 */
const chartData = computed(() => {
  const now = new Date()
  const weeks = []
  const counts = []

  // Generate last 12 weeks
  for (let i = 11; i >= 0; i--) {
    const weekStart = new Date(now.getTime() - i * 7 * 24 * 60 * 60 * 1000)
    const weekStartNormalized = getWeekStart(weekStart)
    weeks.push({
      label: getWeekLabel(weekStartNormalized),
      start: weekStartNormalized,
      end: new Date(weekStartNormalized.getTime() + 7 * 24 * 60 * 60 * 1000),
      count: 0
    })
  }

  // Count applications per week
  props.applications.forEach(app => {
    if (!app.applied_date) return

    const appliedDate = new Date(app.applied_date)

    for (const week of weeks) {
      if (appliedDate >= week.start && appliedDate < week.end) {
        week.count++
        break
      }
    }
  })

  const labels = weeks.map(w => w.label)
  const data = weeks.map(w => w.count)

  return {
    labels,
    datasets: [
      {
        label: 'Applications',
        data,
        fill: true,
        borderColor: '#3B82F6', // blue-500
        backgroundColor: 'rgba(59, 130, 246, 0.1)', // blue-500 with transparency
        tension: 0.4, // Smooth curves
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: '#3B82F6',
        pointBorderColor: '#1E293B', // slate-800
        pointBorderWidth: 2,
        pointHoverBackgroundColor: '#60A5FA', // blue-400
        pointHoverBorderColor: '#1E293B',
        borderWidth: 3
      }
    ]
  }
})

/**
 * Chart options
 */
const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false
  },
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      backgroundColor: '#1E293B', // slate-800
      titleColor: '#F1F5F9', // slate-100
      bodyColor: '#E2E8F0', // slate-200
      borderColor: '#334155', // slate-700
      borderWidth: 1,
      padding: 12,
      displayColors: true,
      callbacks: {
        label: function(context) {
          const label = context.dataset.label || ''
          const value = context.parsed.y
          return `${label}: ${value} application${value !== 1 ? 's' : ''}`
        }
      }
    }
  },
  scales: {
    x: {
      grid: {
        color: '#334155', // slate-700
        drawBorder: false
      },
      ticks: {
        color: '#94A3B8', // slate-400
        font: {
          size: 11,
          weight: 'bold'
        }
      }
    },
    y: {
      beginAtZero: true,
      grid: {
        color: '#334155', // slate-700
        drawBorder: false
      },
      ticks: {
        color: '#94A3B8', // slate-400
        font: {
          size: 11,
          weight: 'bold'
        },
        stepSize: 1
      }
    }
  }
}))
</script>

<template>
  <div class="h-full w-full p-4">
    <Line
      :data="chartData"
      :options="chartOptions"
    />
  </div>
</template>

<style scoped>
/* Chart container */
</style>
