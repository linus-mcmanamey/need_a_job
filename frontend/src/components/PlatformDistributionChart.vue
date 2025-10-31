<script setup>
import { computed } from 'vue'
import { Pie } from 'vue-chartjs'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  CategoryScale
} from 'chart.js'

// Register Chart.js components
ChartJS.register(Title, Tooltip, Legend, ArcElement, CategoryScale)

// Props
const props = defineProps({
  platformDistribution: {
    type: Object,
    required: true,
    default: () => ({})
  }
})

// Platform colors and icons
const platformConfig = {
  linkedin: { color: '#0077B5', icon: '💼', label: 'LinkedIn' },
  seek: { color: '#F05252', icon: '🔍', label: 'SEEK' },
  indeed: { color: '#2164F3', icon: '📍', label: 'Indeed' },
  default: { color: '#6B7280', icon: '🔗', label: 'Other' }
}

/**
 * Chart data computed from platform distribution
 */
const chartData = computed(() => {
  const platforms = Object.keys(props.platformDistribution)

  if (platforms.length === 0) {
    return {
      labels: ['No Data'],
      datasets: [{
        data: [1],
        backgroundColor: ['#374151'],
        borderColor: ['#1F2937'],
        borderWidth: 2
      }]
    }
  }

  const labels = platforms.map(platform => {
    const config = platformConfig[platform] || platformConfig.default
    return `${config.icon} ${config.label}`
  })

  const data = platforms.map(platform => props.platformDistribution[platform])

  const backgroundColor = platforms.map(platform => {
    const config = platformConfig[platform] || platformConfig.default
    return config.color
  })

  const borderColor = backgroundColor.map(color => {
    // Darker shade for border
    return color + 'DD'
  })

  return {
    labels,
    datasets: [{
      data,
      backgroundColor,
      borderColor,
      borderWidth: 2
    }]
  }
})

/**
 * Chart options
 */
const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        color: '#E2E8F0', // slate-200
        font: {
          size: 12,
          weight: 'bold'
        },
        padding: 15,
        usePointStyle: true,
        pointStyle: 'circle'
      }
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
          const label = context.label || ''
          const value = context.parsed || 0
          const total = context.dataset.data.reduce((acc, val) => acc + val, 0)
          const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0
          return `${label}: ${value} (${percentage}%)`
        }
      }
    }
  }
}))
</script>

<template>
  <div class="h-full w-full flex items-center justify-center p-4">
    <Pie
      :data="chartData"
      :options="chartOptions"
    />
  </div>
</template>

<style scoped>
/* Chart container */
</style>
