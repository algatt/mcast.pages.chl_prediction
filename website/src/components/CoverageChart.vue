<script setup>
import { Bar } from 'vue-chartjs'
import { computed } from 'vue'
import { monthlyCoverage } from '../data/results.js'

const chartData = computed(() => ({
  labels: monthlyCoverage.map(m => m.month),
  datasets: [{
    label: 'Valid-pixel coverage (%)',
    data: monthlyCoverage.map(m => m.coverage),
    backgroundColor: monthlyCoverage.map(m => (['Dec','Jan','Feb'].includes(m.month) ? '#dc2626' : '#0284c7')),
    borderRadius: 4,
  }],
}))

const chartOptions = computed(() => ({
  responsive: true, maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: { callbacks: { label: (ctx) => `${ctx.parsed.y.toFixed(1)}%` } },
  },
  scales: {
    y: { title: { display: true, text: 'Coverage (%)' }, beginAtZero: true, max: 100 },
    x: { title: { display: false } },
  },
}))
</script>

<template>
  <div class="w-full" style="height:280px">
    <Bar :data="chartData" :options="chartOptions" />
  </div>
</template>
