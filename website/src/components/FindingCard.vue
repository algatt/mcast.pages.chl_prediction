<script setup>
defineProps({ finding: { type: Object, required: true } })
</script>

<template>
  <router-link
    :to="'/findings/' + finding.slug"
    class="group evidence-card"
  >
    <div class="evidence-card__top" :data-tone="finding.tone">
      <span class="evidence-card__number">{{ finding.number }}</span>
      <span class="evidence-card__eyebrow">{{ finding.eyebrow }}</span>
      <span aria-hidden="true" class="evidence-card__arrow">↗</span>
    </div>

    <div class="p-6 md:p-7">
      <h3 class="text-xl font-semibold text-ink-950 leading-snug mb-2">
        {{ finding.title }}
      </h3>
      <p class="text-sm font-medium text-slate-500 mb-4">{{ finding.tagline }}</p>
      <p class="text-[15px] text-slate-700 mb-6 leading-relaxed">{{ finding.summary }}</p>

      <div class="pt-5 border-t border-slate-200/80 grid grid-cols-[1fr_auto] gap-4 items-end">
        <div>
          <div class="label-caps">{{ finding.metric.label }}</div>
          <div class="mt-1 text-2xl font-semibold tabular-nums text-ink-950">{{ finding.metric.value }}</div>
        </div>
        <div class="text-xs text-slate-500 max-w-[150px] text-right leading-relaxed">
          {{ finding.metric.vs }}
        </div>
      </div>
    </div>
  </router-link>
</template>
