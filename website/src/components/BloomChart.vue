<script setup>
import { Line } from 'vue-chartjs'
import { computed } from 'vue'
import { HORIZONS, bloomSkill, bloomPOD, bloomFAR } from '../data/results.js'

const props = defineProps({
  metric: { type: String, default: 'F1' }, // F1 | POD | FAR
})

const src = computed(() => ({
  F1: bloomSkill, POD: bloomPOD, FAR: bloomFAR,
}[props.metric]))

const chartData = computed(() => ({
  labels: HORIZONS.map(h => `H+${h}`),
  datasets: [
    { label: 'Siegel (median+5%)', data: src.value.siegel,     borderColor: '#1f77b4', backgroundColor: '#1f77b4', tension: 0.3, pointRadius: 4 },
    { label: 'Percentile (P90)',    data: src.value.percentile, borderColor: '#22c55e', backgroundColor: '#22c55e', tension: 0.3, pointRadius: 4, borderDash: [5,4] },
    { label: 'Z-score (>1.5σ)',     data: src.value.zscore,     borderColor: '#dc2626', backgroundColor: '#dc2626', tension: 0.3, pointRadius: 4, borderDash: [2,3] },
  ],
}))

const chartOptions = computed(() => ({
  responsive: true, maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { position: 'bottom', labels: { boxWidth: 12 } },
    tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(3)}` } },
    annotation: {},
  },
  scales: {
    y: {
      title: { display: true, text: props.metric },
      beginAtZero: true, max: 1,
    },
    x: { title: { display: true, text: 'Horizon (days)' } },
  },
}))
</script>

<template>
  <div class="w-full" style="height:340px">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>
