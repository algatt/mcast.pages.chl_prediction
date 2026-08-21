<script setup>
import { Bar } from 'vue-chartjs'
import { computed } from 'vue'
import { monthlyCoverage } from '../data/results.js'

const chartData = computed(() => ({
  labels: monthlyCoverage.map(m => m.month),
  datasets: [
    {
      type: 'bar',
      label: 'Observed CHL-domain coverage',
      data: monthlyCoverage.map(m => m.coverage),
      backgroundColor: monthlyCoverage.map(m => (['Dec', 'Jan', 'Feb'].includes(m.month) ? '#d97706' : '#0f766e')),
      borderRadius: 5,
    },
    {
      type: 'line',
      label: 'Predeclared daily-feasibility threshold',
      data: monthlyCoverage.map(() => 25),
      borderColor: '#e11d48',
      backgroundColor: '#e11d48',
      borderDash: [6, 5],
      borderWidth: 2,
      pointRadius: 0,
    },
  ],
}))

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { position: 'bottom', labels: { boxWidth: 12, color: '#475569' } },
    tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(1)}%` } },
  },
  scales: {
    y: { title: { display: true, text: 'Observed target-domain pixels (%)' }, beginAtZero: true, max: 100 },
    x: { grid: { display: false } },
  },
}))
</script>

<template>
  <div class="w-full" style="height: 300px">
    <Bar :data="chartData" :options="chartOptions" />
  </div>
</template>

