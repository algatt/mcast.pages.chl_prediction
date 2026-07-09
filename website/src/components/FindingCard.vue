<script setup>
defineProps({ finding: { type: Object, required: true } })
</script>

<template>
  <router-link
    :to="'/findings/' + finding.slug"
    class="group block relative overflow-hidden rounded-2xl shadow-sm border border-slate-200 bg-white card-hover"
  >
    <!-- gradient stripe -->
    <div :class="'h-2 bg-gradient-to-r ' + finding.color" />

    <div class="p-6">
      <div class="flex items-start justify-between mb-3">
        <div class="flex items-center gap-2">
          <span class="text-3xl">{{ finding.icon }}</span>
          <span class="text-xs font-mono font-bold text-slate-400">Finding {{ finding.number }}</span>
        </div>
        <span class="text-sm text-ocean-600 opacity-0 group-hover:opacity-100 transition-opacity">→</span>
      </div>

      <h3 class="text-lg font-bold text-slate-900 leading-tight mb-2">
        {{ finding.title }}
      </h3>
      <p class="text-sm text-slate-500 mb-4">{{ finding.tagline }}</p>
      <p class="text-sm text-slate-700 mb-5 leading-relaxed">{{ finding.summary }}</p>

      <div class="pt-4 border-t border-slate-100 flex items-baseline justify-between">
        <div>
          <div class="text-xs uppercase tracking-wide text-slate-400 font-semibold">{{ finding.metric.label }}</div>
          <div class="text-2xl font-bold tabular-nums text-slate-900">{{ finding.metric.value }}</div>
        </div>
        <div class="text-xs text-slate-500 max-w-[150px] text-right">{{ finding.metric.vs }}</div>
      </div>
    </div>
  </router-link>
</template>
