<script setup>
import { Bar } from 'vue-chartjs'
import { computed } from 'vue'
import { groupImportance } from '../data/results.js'

const props = defineProps({ view: { type: String, default: 'abl' } })

const chartData = computed(() => {
  const groups = [...groupImportance].sort((a, b) => a.abl - b.abl)
  const datasets = []
  if (props.view === 'perm' || props.view === 'both') {
    datasets.push({
      label: 'Permutation ΔRMSE (validation)',
      data: groups.map(g => g.perm),
      backgroundColor: '#0891b2',
      borderRadius: 4,
    })
  }
  if (props.view === 'abl' || props.view === 'both') {
    datasets.push({
      label: 'Ablation |ΔR²| when dropped',
      data: groups.map(g => -g.abl),
      backgroundColor: groups.map(g => g.abl <= -0.005 ? '#e11d48' : g.abl <= -0.002 ? '#d97706' : '#94a3b8'),
      borderRadius: 4,
    })
  }
  return { labels: groups.map(g => g.group), datasets }
})

const chartOptions = computed(() => ({
  indexAxis: 'y',
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom', labels: { boxWidth: 12, color: '#475569' } },
    tooltip: {
      callbacks: {
        label: (ctx) => {
          const g = groupImportance.find(x => x.group === ctx.label)
          return ctx.dataset.label.startsWith('Ablation')
            ? `Ablation ΔR²: ${g.abl.toFixed(4)}`
            : `Permutation ΔRMSE: +${g.perm.toFixed(4)} ± ${g.permStd.toFixed(4)}`
        },
      },
    },
  },
  scales: {
    x: { title: { display: true, text: props.view === 'both' ? 'Metric magnitude — compare within a series only' : 'Metric magnitude' } },
    y: { grid: { display: false } },
  },
}))
</script>

<template>
  <div class="w-full" style="height: 360px">
    <Bar :data="chartData" :options="chartOptions" />
  </div>
</template>

