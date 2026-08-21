<script setup>
import { computed, ref } from 'vue'
import SectionHeader from '../components/SectionHeader.vue'
import { phases, stages } from '../data/stages.js'

const activePhase = ref('All')
const visibleStages = computed(() => activePhase.value === 'All'
  ? stages
  : stages.filter(stage => stage.phase === activePhase.value))
</script>

<template>
  <div>
    <section class="border-b border-slate-200 bg-white">
      <div class="container-page py-12 md:py-16">
        <SectionHeader
          eyebrow="Methods · 13 notebooks · 13 gates"
          title="A pipeline built as a chain of falsifiable contracts"
          lead="Every stage answers one scientific question, checks the answer programmatically, and leaves a named artifact for the next notebook. Select a phase for a shorter view or read the full sequence."
        />

        <div class="method-contract">
          <div>
            <span class="method-contract__n">01</span>
            <p><strong>No invented target continuity.</strong> L3 chlorophyll gaps remain missing observations.</p>
          </div>
          <div>
            <span class="method-contract__n">02</span>
            <p><strong>No temporal leakage.</strong> Labels crossing fit or validation boundaries are purged.</p>
          </div>
          <div>
            <span class="method-contract__n">03</span>
            <p><strong>No mismatched comparison.</strong> Model and persistence use identical rows.</p>
          </div>
          <div>
            <span class="method-contract__n">04</span>
            <p><strong>No hidden scale-up.</strong> The three-year run is frozen; expansion needs a new preflight.</p>
          </div>
        </div>
      </div>
    </section>

    <section class="container-page py-12 md:py-16">
      <div class="phase-filter" aria-label="Filter pipeline by phase">
        <button
          v-for="phase in ['All', ...phases]"
          :key="phase"
          type="button"
          :class="{ active: activePhase === phase }"
          @click="activePhase = phase"
        >
          {{ phase }}
        </button>
      </div>

      <ol class="pipeline-list mt-9">
        <li v-for="stage in visibleStages" :key="stage.n" class="pipeline-stage">
          <div class="pipeline-stage__rail">
            <span>{{ stage.n }}</span>
            <i></i>
          </div>

          <article>
            <header class="pipeline-stage__header">
              <div>
                <div class="flex flex-wrap items-center gap-2">
                  <span class="stage-phase">{{ stage.phase }}</span>
                  <code>{{ stage.notebook }}</code>
                </div>
                <h2>{{ stage.title }}</h2>
                <p class="pipeline-stage__question">{{ stage.question }}</p>
              </div>
              <div class="pipeline-stage__metric">{{ stage.metric }}</div>
            </header>

            <div class="pipeline-stage__body" :class="{ 'has-figure': stage.figure }">
              <div class="space-y-5">
                <div>
                  <div class="label-caps">Method</div>
                  <p>{{ stage.method }}</p>
                </div>
                <div class="gate-box">
                  <div class="gate-box__label"><span></span> Validation gate</div>
                  <p>{{ stage.gate }}</p>
                </div>
                <div class="result-box">
                  <div>
                    <span>Outcome</span>
                    <strong>{{ stage.result }}</strong>
                  </div>
                  <div v-if="stage.artifact">
                    <span>Handoff artifact</span>
                    <code>{{ stage.artifact }}</code>
                  </div>
                </div>
              </div>

              <figure v-if="stage.figure" class="pipeline-figure">
                <img :src="`figs/${stage.figure}`" :alt="`Stage ${stage.n}: ${stage.title}`" loading="lazy" />
                <figcaption>
                  Visual evidence from {{ stage.notebook }}. The captioned method and gate specify what the figure can—and cannot—support.
                </figcaption>
              </figure>
            </div>
          </article>
        </li>
      </ol>

      <div class="mt-12 flex flex-wrap items-center justify-between gap-4 border-t border-slate-200 pt-8">
        <p class="text-sm text-slate-500">Next: inspect source identity, coverage and feature provenance.</p>
        <router-link to="/data" class="button-dark">Open data & evidence →</router-link>
      </div>
    </section>
  </div>
</template>

<style scoped>
.method-contract {
  @apply grid md:grid-cols-2 xl:grid-cols-4 border border-slate-200 rounded-2xl overflow-hidden;
}
.method-contract > div {
  @apply p-5 bg-[#f8faf9] border-b md:border-r border-slate-200 last:border-0;
}
.method-contract__n {
  @apply font-mono text-[10px] text-teal-700;
}
.method-contract p {
  @apply mt-2 text-sm leading-relaxed text-slate-600;
}
.method-contract strong { @apply text-ink-950 font-semibold; }
.phase-filter {
  @apply flex gap-2 overflow-x-auto pb-2;
  scrollbar-width: thin;
}
.phase-filter button {
  @apply shrink-0 px-3.5 py-2 rounded-full border border-slate-300 bg-white text-xs font-medium text-slate-600 hover:border-teal-300 hover:text-teal-800 transition-colors;
}
.phase-filter button.active {
  @apply border-ink-950 bg-ink-950 text-white;
}
.pipeline-list { @apply space-y-7; }
.pipeline-stage { @apply grid grid-cols-[2.7rem_1fr] gap-3 md:grid-cols-[4rem_1fr] md:gap-5; }
.pipeline-stage__rail { @apply flex flex-col items-center; }
.pipeline-stage__rail span {
  @apply w-10 h-10 md:w-12 md:h-12 rounded-full border border-teal-300 bg-white grid place-items-center font-mono text-xs font-semibold text-teal-800;
}
.pipeline-stage__rail i { @apply w-px flex-1 bg-slate-300 mt-2; }
.pipeline-stage:last-child .pipeline-stage__rail i { @apply hidden; }
.pipeline-stage article {
  @apply mb-1 rounded-2xl border border-slate-200 bg-white overflow-hidden;
  box-shadow: 0 14px 46px rgba(15, 23, 42, 0.05);
}
.pipeline-stage__header {
  @apply p-5 md:p-7 grid md:grid-cols-[1fr_auto] gap-5 border-b border-slate-200 bg-slate-50/60;
}
.stage-phase { @apply font-mono text-[10px] uppercase tracking-[0.12em] font-semibold text-teal-700; }
.pipeline-stage__header code { @apply font-mono text-[10px] text-slate-400; }
.pipeline-stage__header h2 { @apply mt-3 text-2xl font-semibold tracking-[-0.025em] text-ink-950; }
.pipeline-stage__question { @apply mt-2 text-sm md:text-base text-slate-600 leading-relaxed; }
.pipeline-stage__metric { @apply self-start rounded-lg border border-teal-200 bg-teal-50 px-3 py-2 font-mono text-[11px] font-semibold text-teal-900 tabular-nums; }
.pipeline-stage__body { @apply p-5 md:p-7; }
.pipeline-stage__body.has-figure { @apply grid xl:grid-cols-[1.05fr_.95fr] gap-7 items-start; }
.pipeline-stage__body p { @apply mt-2 text-sm leading-relaxed text-slate-700; }
.gate-box { @apply rounded-xl border border-amber-200 bg-amber-50/60 p-4; }
.gate-box__label { @apply flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.12em] font-semibold text-amber-800; }
.gate-box__label span { @apply w-1.5 h-1.5 rounded-full bg-amber-500; }
.result-box { @apply grid sm:grid-cols-2 gap-4 pt-1; }
.result-box > div { @apply rounded-xl border border-slate-200 p-4; }
.result-box span { @apply block font-mono text-[9px] uppercase tracking-[0.12em] text-slate-400; }
.result-box strong { @apply block mt-2 text-sm leading-relaxed font-semibold text-ink-950; }
.result-box code { @apply block mt-2 text-xs text-teal-800 break-all; }
.pipeline-figure { @apply rounded-xl border border-slate-200 bg-[#f8faf9] p-3; }
.pipeline-figure img { @apply w-full h-auto rounded-lg; }
.pipeline-figure figcaption { @apply mt-3 text-[11px] leading-relaxed text-slate-500; }
</style>
