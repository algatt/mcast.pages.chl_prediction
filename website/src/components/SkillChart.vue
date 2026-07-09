<script setup>
import { Line } from 'vue-chartjs'
import { computed } from 'vue'
import { HORIZONS, persistence, climatology, xgbV2Single, xgbV2WalkForward } from '../data/results.js'

const props = defineProps({
  metric:  { type: String, default: 'r2' },   // 'r2' | 'rmse'
  showWF:  { type: Boolean, default: true },
})

const chartData = computed(() => {
  const label = props.metric === 'r2' ? 'R²' : 'RMSE'
  const persArr = props.metric === 'r2' ? persistence.r2 : persistence.rmse
  const climArr = props.metric === 'r2' ? climatology.r2 : climatology.rmse
  const v2SArr  = props.metric === 'r2' ? xgbV2Single.r2 : xgbV2Single.rmse
  const wfMean  = props.metric === 'r2' ? xgbV2WalkForward.r2_mean : xgbV2WalkForward.rmse_mean
  const wfStd   = props.metric === 'r2' ? xgbV2WalkForward.r2_std  : xgbV2WalkForward.rmse_std
  const wfHi    = wfMean.map((m, i) => m + wfStd[i])
  const wfLo    = wfMean.map((m, i) => m - wfStd[i])

  const datasets = [
    { label: `Persistence`, data: persArr, borderColor: '#94a3b8', backgroundColor: '#94a3b8', borderDash: [4, 4], tension: 0.3, pointRadius: 3 },
    { label: `Climatology`, data: climArr, borderColor: '#a3a3a3', backgroundColor: '#a3a3a3', borderDash: [1, 3], tension: 0.3, pointRadius: 3 },
    { label: `XGB v2 (single-split)`, data: v2SArr, borderColor: '#0284c7', backgroundColor: '#0284c7', tension: 0.3, pointRadius: 4 },
  ]
  if (props.showWF) {
    datasets.push(
      { label: `XGB v2 (walk-forward, mean +σ)`, data: wfHi, borderColor: 'rgba(220,38,38,0.25)', backgroundColor: 'rgba(220,38,38,0.12)', pointRadius: 0, borderWidth: 0, fill: '+1', tension: 0.3 },
      { label: `XGB v2 (walk-forward, mean −σ)`, data: wfLo, borderColor: 'rgba(220,38,38,0.25)', backgroundColor: 'rgba(220,38,38,0.12)', pointRadius: 0, borderWidth: 0, tension: 0.3 },
      { label: `XGB v2 (walk-forward, mean)`,    data: wfMean, borderColor: '#dc2626', backgroundColor: '#dc2626', tension: 0.3, pointRadius: 4, borderWidth: 2.5 },
    )
  }
  return {
    labels: HORIZONS.map(h => `H+${h}`),
    datasets,
  }
})

const chartOptions = computed(() => ({
  responsive: true, maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { position: 'bottom', labels: { boxWidth: 12, filter: (item) => !item.text.includes('mean +') && !item.text.includes('mean −') } },
    tooltip: {
      callbacks: {
        label: (ctx) => {
          if (ctx.dataset.label?.includes('mean +') || ctx.dataset.label?.includes('mean −')) return null
          return `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(3)}`
        },
      },
    },
  },
  scales: {
    y: { title: { display: true, text: props.metric === 'r2' ? 'R²' : 'RMSE (log10 mg m⁻³)' }, beginAtZero: props.metric === 'r2', suggestedMax: props.metric === 'r2' ? 1 : undefined },
    x: { title: { display: true, text: 'Horizon (days)' } },
  },
}))
</script>

<template>
  <div class="w-full" style="height:340px">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>
