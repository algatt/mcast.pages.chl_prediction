<script setup>
import { Bar } from 'vue-chartjs'
import { computed } from 'vue'
import { perFoldH3 } from '../data/results.js'

const chartData = computed(() => ({
  labels: perFoldH3.map(f => f.quarter),
  datasets: [
    { label: 'XGBoost v2', data: perFoldH3.map(f => f.r2), backgroundColor: '#0f766e', borderRadius: 4 },
    { label: 'Persistence — matched rows', data: perFoldH3.map(f => f.persistence), backgroundColor: '#cbd5e1', borderRadius: 4 },
  ],
}))

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { position: 'bottom', labels: { boxWidth: 12, color: '#475569' } },
    tooltip: {
      callbacks: {
        afterTitle: (items) => perFoldH3[items[0].dataIndex].kind,
        label: (ctx) => `${ctx.dataset.label}: R² = ${ctx.parsed.y.toFixed(3)}`,
      },
    },
  },
  scales: {
    y: { title: { display: true, text: 'Quarterly test R² at H+3' }, beginAtZero: true, max: 1 },
    x: { grid: { display: false } },
  },
}))
</script>

<template>
  <div class="w-full" style="height: 320px">
    <Bar :data="chartData" :options="chartOptions" />
  </div>
</template>

