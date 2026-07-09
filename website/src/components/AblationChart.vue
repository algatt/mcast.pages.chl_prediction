<script setup>
import { Bar } from 'vue-chartjs'
import { computed } from 'vue'
import { groupImportance } from '../data/results.js'

const props = defineProps({
  view: { type: String, default: 'both' }, // 'perm' | 'abl' | 'both'
})

const chartData = computed(() => {
  const groups = [...groupImportance].sort((a, b) => a.abl - b.abl) // most essential first
  const labels = groups.map(g => g.group)
  const permData = groups.map(g => g.perm)
  // ablation ΔR² are negative; show absolute for readability, then colour by essentiality
  const ablData = groups.map(g => -g.abl)
  const ablColors = groups.map(g => g.abl <= -0.005 ? '#dc2626' : g.abl <= -0.002 ? '#f59e0b' : '#94a3b8')

  const datasets = []
  if (props.view === 'perm' || props.view === 'both')
    datasets.push({ label: 'Permutation ΔRMSE (val)', data: permData, backgroundColor: '#0284c7' })
  if (props.view === 'abl' || props.view === 'both')
    datasets.push({ label: 'Ablation |ΔR²| when dropped', data: ablData, backgroundColor: ablColors })
  return { labels, datasets }
})

const chartOptions = computed(() => ({
  indexAxis: 'y',
  responsive: true, maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom' },
    tooltip: {
      callbacks: {
        label: (ctx) => {
          if (ctx.dataset.label.startsWith('Ablation')) {
            const g = groupImportance.find(x => x.group === ctx.label)
            return `Ablation ΔR² = ${g.abl.toFixed(4)} (removing hurts by this)`
          }
          return `${ctx.dataset.label}: ${ctx.parsed.x.toFixed(4)}`
        },
      },
    },
  },
  scales: {
    x: { title: { display: true, text: 'Contribution (larger = more essential)' } },
    y: { grid: { display: false } },
  },
}))
</script>

<template>
  <div class="w-full" style="height:360px">
    <Bar :data="chartData" :options="chartOptions" />
  </div>
</template>
