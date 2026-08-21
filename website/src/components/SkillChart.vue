<script setup>
import { Line } from 'vue-chartjs'
import { computed } from 'vue'
import {
  HORIZONS,
  walkForwardPersistence,
  xgbV2Single,
  xgbV2WalkForward,
} from '../data/results.js'

const props = defineProps({
  metric:  { type: String, default: 'r2' },   // 'r2' | 'rmse'
  showWF:  { type: Boolean, default: true },
})

const chartData = computed(() => {
  const persArr = props.metric === 'r2'
    ? walkForwardPersistence.r2_mean
    : walkForwardPersistence.rmse_mean
  const v2SArr  = props.metric === 'r2' ? xgbV2Single.r2 : xgbV2Single.rmse
  const wfMean  = props.metric === 'r2' ? xgbV2WalkForward.r2_mean : xgbV2WalkForward.rmse_mean
  const wfStd   = props.metric === 'r2' ? xgbV2WalkForward.r2_std  : xgbV2WalkForward.rmse_std
  const wfHi    = wfMean.map((m, i) => m + wfStd[i])
  const wfLo    = wfMean.map((m, i) => m - wfStd[i])

  const datasets = [
    { label: `Persistence · matched folds`, data: persArr, borderColor: '#64748b', backgroundColor: '#64748b', borderDash: [5, 5], tension: 0.25, pointRadius: 3 },
    { label: `XGBoost v2 · single split`, data: v2SArr, borderColor: '#0891b2', backgroundColor: '#0891b2', borderDash: [2, 3], tension: 0.25, pointRadius: 3 },
  ]
  if (props.showWF) {
    datasets.push(
      { label: `Walk-forward · mean + SD`, data: wfHi, borderColor: 'rgba(20,184,166,0)', backgroundColor: 'rgba(20,184,166,0.14)', pointRadius: 0, borderWidth: 0, fill: '+1', tension: 0.25 },
      { label: `Walk-forward · mean − SD`, data: wfLo, borderColor: 'rgba(20,184,166,0)', backgroundColor: 'rgba(20,184,166,0.14)', pointRadius: 0, borderWidth: 0, tension: 0.25 },
      { label: `XGBoost v2 · walk-forward mean`, data: wfMean, borderColor: '#0f766e', backgroundColor: '#0f766e', tension: 0.25, pointRadius: 4, borderWidth: 2.5 },
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
    legend: {
      position: 'bottom',
      labels: {
        color: '#334155',
        boxWidth: 12,
        padding: 18,
        filter: (item) => !item.text.includes('mean +') && !item.text.includes('mean −'),
      },
    },
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
    y: {
      title: { display: true, text: props.metric === 'r2' ? 'R²' : 'RMSE (log10 mg m⁻³)', color: '#475569' },
      beginAtZero: props.metric === 'r2',
      suggestedMax: props.metric === 'r2' ? 1 : undefined,
      grid: { color: 'rgba(148,163,184,0.18)' },
      ticks: { color: '#64748b' },
    },
    x: {
      title: { display: true, text: 'Forecast horizon (days)', color: '#475569' },
      grid: { display: false },
      ticks: { color: '#64748b' },
    },
  },
}))
</script>

<template>
  <div class="w-full" style="height:340px">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>
