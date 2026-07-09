<script setup>
import { Bar } from 'vue-chartjs'
import { computed } from 'vue'
import { perFoldH3 } from '../data/results.js'

const COLORS = {
  winter: '#dc2626', spring: '#22c55e', summer: '#f59e0b', autumn: '#ea580c',
}

const chartData = computed(() => ({
  labels: perFoldH3.map(f => f.quarter),
  datasets: [{
    label: 'Fold R² at H+3',
    data:  perFoldH3.map(f => f.r2),
    backgroundColor: perFoldH3.map(f => COLORS[f.kind]),
    borderRadius: 4,
  }],
}))

const chartOptions = computed(() => ({
  responsive: true, maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx) => {
          const f = perFoldH3[ctx.dataIndex]
          return `${f.quarter} (${f.kind}): R² = ${f.r2.toFixed(3)}`
        },
      },
    },
  },
  scales: {
    y: { title: { display: true, text: 'Test R² at H+3' }, beginAtZero: true, max: 1 },
  },
}))
</script>

<template>
  <div>
    <div class="w-full" style="height:300px">
      <Bar :data="chartData" :options="chartOptions" />
    </div>
    <div class="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-600">
      <span class="inline-flex items-center gap-1.5"><span class="w-3 h-3 rounded-sm inline-block" style="background:#dc2626"></span>winter</span>
      <span class="inline-flex items-center gap-1.5"><span class="w-3 h-3 rounded-sm inline-block" style="background:#22c55e"></span>spring</span>
      <span class="inline-flex items-center gap-1.5"><span class="w-3 h-3 rounded-sm inline-block" style="background:#f59e0b"></span>summer</span>
      <span class="inline-flex items-center gap-1.5"><span class="w-3 h-3 rounded-sm inline-block" style="background:#ea580c"></span>autumn</span>
    </div>
  </div>
</template>
