<script setup>
import { Line } from 'vue-chartjs'
import { computed } from 'vue'
import { HORIZONS, bloomSkill, bloomPOD, bloomFAR } from '../data/results.js'

const props = defineProps({ metric: { type: String, default: 'F1' } })
const src = computed(() => ({ F1: bloomSkill, POD: bloomPOD, FAR: bloomFAR }[props.metric]))

const chartData = computed(() => ({
  labels: HORIZONS.map(h => `H+${h}`),
  datasets: [
    { label: 'Median + 5% (auxiliary regime)', data: src.value.median5, borderColor: '#64748b', backgroundColor: '#64748b', tension: 0.3, pointRadius: 3, borderDash: [2, 4] },
    { label: 'Monthly P90 (rare event)', data: src.value.percentile, borderColor: '#0f766e', backgroundColor: '#0f766e', tension: 0.3, pointRadius: 4 },
    { label: 'Z-score > 1.5σ (rare event)', data: src.value.zscore, borderColor: '#e11d48', backgroundColor: '#e11d48', tension: 0.3, pointRadius: 4, borderDash: [6, 4] },
  ],
}))

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { position: 'bottom', labels: { boxWidth: 12, color: '#475569' } },
    tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(3)}` } },
  },
  scales: {
    y: { title: { display: true, text: props.metric }, beginAtZero: true, max: 1 },
    x: { title: { display: true, text: 'Forecast horizon (days)' }, grid: { display: false } },
  },
}))
</script>

<template>
  <div class="w-full" style="height: 340px">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>

