<script setup>
import SectionHeader from '../components/SectionHeader.vue'
import CoverageChart from '../components/CoverageChart.vue'

const sources = [
  { role: 'Target', name: 'Chlorophyll-a', source: 'CMEMS Ocean Colour', product: 'cmems_obs-oc_med_bgc-plankton_my_l3-multi-1km_P1D', version: '202411', native: '1 km · daily L3', vars: 'CHL', handling: 'Provider limits; no gap fill' },
  { role: 'Base predictor', name: 'Sea-surface temperature', source: 'CMEMS SST', product: 'cmems_SST_MED_SST_L4_REP_OBSERVATIONS_010_021', version: '202411', native: '~5 km · daily L4', vars: 'analysed_sst', handling: 'Exact daily axis; interpolate spatially' },
  { role: 'Static predictor', name: 'Bathymetry', source: 'NOAA ETOPO 2022', product: 'ETOPO 2022 · 15 arc-second', version: '2022', native: '~460 m · static', vars: 'elevation', handling: 'Convert negative elevation to depth' },
  { role: 'Stage 8', name: 'Surface salinity', source: 'CMEMS Physics', product: 'cmems_mod_med_phy-sal_my_4.2km_P1D-m', version: '202511', native: '4.2 km · daily', vars: 'so', handling: 'Single 0–2 m layer; halo' },
  { role: 'Stage 8', name: 'Surface currents', source: 'CMEMS Physics', product: 'cmems_mod_med_phy-cur_my_4.2km_P1D-m', version: '202511', native: '4.2 km · daily', vars: 'uo, vo', handling: 'Single 0–2 m layer; halo' },
  { role: 'Stage 8', name: 'Sea-surface height', source: 'CMEMS Physics', product: 'cmems_mod_med_phy-ssh_my_4.2km_P1D-m', version: '202511', native: '4.2 km · daily', vars: 'zos', handling: 'Exact daily axis; halo' },
  { role: 'Stage 8', name: 'Mixed-layer depth', source: 'CMEMS Physics', product: 'cmems_mod_med_phy-mld_my_4.2km_P1D-m', version: '202511', native: '4.2 km · daily', vars: 'mlotst', handling: 'Exact daily axis; halo' },
  { role: 'Stage 8', name: 'Optical attenuation', source: 'CMEMS Ocean Colour', product: 'cmems_obs-oc_med_bgc-transp_my_l3-multi-1km_P1D', version: '202311', native: '1 km · daily L3', vars: 'KD490', handling: 'Native cloud gaps retained' },
  { role: 'Stage 8', name: '10 m wind', source: 'ECMWF ERA5', product: 'reanalysis-era5-single-levels', version: 'retrieved 2026', native: '~31 km · hourly', vars: 'u10, v10', handling: '24 hours/day → daily arithmetic mean' },
]

const featureGroups = [
  { group: 'CHL history', count: 9, examples: 't0; lags 1/2/3/7/14; rolling mean/std; gap age' },
  { group: 'SST', count: 3, examples: 't0; lag 1; 7-day mean' },
  { group: 'Static & time', count: 3, examples: 'depth; sin/cos day of year' },
  { group: 'Salinity', count: 2, examples: 'daily; 7-day mean' },
  { group: 'Currents & SSH', count: 4, examples: 'u, v, speed, SSH' },
  { group: 'Mixed layer', count: 3, examples: 'daily; lag 1; 7-day mean' },
  { group: 'Optics', count: 2, examples: 'KD490; 7-day mean' },
  { group: 'Wind', count: 6, examples: 'u, v, speed, 3/7-day means, stress-curl proxy' },
]
</script>

<template>
  <div class="container-page py-12 md:py-16">
    <SectionHeader
      eyebrow="Source identity · coverage · feature provenance"
      title="The data contract is stricter than “same region, same dates”"
      lead="Every dynamic source must have the exact 2021–2023 daily axis and a grid that surrounds the CHL domain. Spatial interpolation is allowed for predictors; temporal substitution and target gap-filling are not."
    />

    <section class="data-overview">
      <div>
        <span>Study box</span>
        <strong>35.5–37.5° N<br />12.0–15.5° E</strong>
      </div>
      <div>
        <span>Observed target domain</span>
        <strong>46,158 pixels</strong>
      </div>
      <div>
        <span>Study period</span>
        <strong>1,095 daily maps</strong>
      </div>
      <div>
        <span>Supervised sample</span>
        <strong>360,000 rows</strong>
      </div>
    </section>

    <section class="mt-14 grid lg:grid-cols-[1fr_.9fr] gap-8 items-start">
      <div>
        <div class="label-caps">Why L3 matters</div>
        <h2 class="section-title mt-3">Missing means unobserved—not zero, and not reconstructed.</h2>
        <div class="mt-5 space-y-4 text-slate-600 leading-relaxed">
          <p>
            The CHL target is a daily Level-3 satellite product. Clouds and retrieval failures remain
            NaN. Models train only where a future target is observed, while missing current CHL is kept
            in the feature matrix for XGBoost’s native missing-value handling.
          </p>
          <p>
            The observable domain contains pixels with at least one valid CHL retrieval in the study
            period. This removes never-observable land/outside pixels from the coverage denominator
            without pretending cloudy days were observed.
          </p>
        </div>
        <div class="definition-grid mt-7">
          <div><span>Allowed</span><p>Spatial interpolation of predictors onto CHL coordinates.</p></div>
          <div><span>Not allowed</span><p>Target gap filling or nearest-time predictor substitution.</p></div>
          <div><span>Preserved</span><p>NaN in CHL history, KD490 and cloudy issue-time rows.</p></div>
          <div><span>Separated</span><p>All-target model scores from persistence-comparison scores.</p></div>
        </div>
      </div>

      <figure class="figure-evidence">
        <img :src="'figs/02_coverage_map.png'" alt="Map of valid-day fraction over the observable chlorophyll domain" />
        <figcaption>
          <strong>Observable-domain coverage.</strong> Colour shows the fraction of 2021–2023 days with a valid CHL retrieval. Grey is outside the target domain—not a zero-valued ocean pixel.
        </figcaption>
      </figure>
    </section>

    <section class="mt-16 md:mt-20">
      <div class="section-intro">
        <div>
          <div class="label-caps">Gate 2 · target-mode decision</div>
          <h2>Winter coverage supported a daily target</h2>
        </div>
        <p>
          DJF coverage is 50.47%, above the 25% feasibility threshold. The record still contains
          87 zero-coverage days and 302 days below the threshold; the decision says daily sampling is
          viable, not that missingness is harmless.
        </p>
      </div>
      <div class="chart-panel mt-8">
        <CoverageChart />
        <p class="chart-note">
          Red bars are DJF. Coverage is the daily valid-pixel fraction within the observable target domain,
          averaged by calendar month. The dashed decision threshold is 25%.
        </p>
      </div>
    </section>

    <section class="mt-16 md:mt-20">
      <div class="label-caps">Pinned sources used in the frozen run</div>
      <h2 class="section-title mt-3">Dataset ledger</h2>
      <p class="mt-4 max-w-3xl text-slate-600 leading-relaxed">
        Version labels below describe the validated acquisition. A future scale-up must query the
        catalogues again rather than assuming the same identifiers or coverage remain available.
      </p>

      <div class="source-table-wrap mt-8">
        <table class="source-table">
          <thead>
            <tr><th>Role / source</th><th>Dataset</th><th>Native support</th><th>Variables & handling</th></tr>
          </thead>
          <tbody>
            <tr v-for="source in sources" :key="source.product">
              <td><span>{{ source.role }}</span><strong>{{ source.name }}</strong><small>{{ source.source }}</small></td>
              <td><code>{{ source.product }}</code><small>version {{ source.version }}</small></td>
              <td>{{ source.native }}</td>
              <td><code>{{ source.vars }}</code><small>{{ source.handling }}</small></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="mt-16 md:mt-20 grid lg:grid-cols-[.85fr_1.15fr] gap-9 items-start">
      <div>
        <div class="label-caps">Final model schema</div>
        <h2 class="section-title mt-3">32 features in eight evidence-tested groups</h2>
        <p class="mt-5 text-slate-600 leading-relaxed">
          Stage 8b joins the new predictors to the exact Notebook 4 sample keys. No second sampling draw
          changes the rows. All groups were retained because each passed both ablation and grouped
          permutation criteria at H+3.
        </p>
        <router-link to="/findings/group-ablation" class="text-link mt-6 inline-flex">See the selection evidence →</router-link>
      </div>
      <div class="feature-ledger">
        <div v-for="item in featureGroups" :key="item.group">
          <span class="feature-ledger__count">{{ item.count }}</span>
          <div><strong>{{ item.group }}</strong><p>{{ item.examples }}</p></div>
        </div>
        <footer><span>Total</span><strong>32</strong></footer>
      </div>
    </section>

    <div class="mt-16 flex flex-wrap justify-between gap-4 border-t border-slate-200 pt-8">
      <router-link to="/methodology" class="button-light">← Pipeline</router-link>
      <router-link to="/forecast" class="button-dark">Visual diagnostics →</router-link>
    </div>
  </div>
</template>

<style scoped>
.data-overview { @apply grid sm:grid-cols-2 lg:grid-cols-4 border border-slate-200 bg-white rounded-2xl overflow-hidden; }
.data-overview > div { @apply p-5 border-b sm:border-r border-slate-200 last:border-0; }
.data-overview span { @apply block font-mono text-[9px] uppercase tracking-[0.13em] text-slate-400; }
.data-overview strong { @apply block mt-2 text-lg font-semibold text-ink-950 leading-snug tabular-nums; }
.definition-grid { @apply grid sm:grid-cols-2 gap-3; }
.definition-grid > div { @apply rounded-xl border border-slate-200 bg-white p-4; }
.definition-grid span { @apply font-mono text-[9px] uppercase tracking-[0.12em] font-semibold text-teal-700; }
.definition-grid p { @apply mt-2 text-sm leading-relaxed text-slate-600; }
.figure-evidence { @apply rounded-2xl border border-slate-200 bg-white p-3; box-shadow: 0 16px 48px rgba(15,23,42,.06); }
.figure-evidence img { @apply w-full h-auto rounded-xl; }
.figure-evidence figcaption { @apply p-3 pb-1 text-xs leading-relaxed text-slate-500; }
.figure-evidence strong { @apply text-ink-950; }
.chart-note { @apply mt-4 pt-4 border-t border-slate-200 text-xs leading-relaxed text-slate-500; }
.source-table-wrap { @apply overflow-x-auto rounded-2xl border border-slate-200 bg-white; }
.source-table { @apply w-full text-left text-sm; min-width: 860px; }
.source-table th { @apply px-5 py-3 bg-slate-50 border-b border-slate-200 font-mono text-[9px] uppercase tracking-[.12em] text-slate-500; }
.source-table td { @apply px-5 py-4 align-top border-b border-slate-100 text-slate-600; }
.source-table tr:last-child td { @apply border-0; }
.source-table td > span,.source-table td > strong,.source-table td > small { @apply block; }
.source-table td > span { @apply font-mono text-[9px] uppercase tracking-[.1em] text-teal-700; }
.source-table td > strong { @apply mt-1 text-ink-950; }
.source-table td > small { @apply mt-1 text-[11px] text-slate-400; }
.source-table code { @apply block font-mono text-[11px] leading-relaxed text-slate-700 break-all; }
.feature-ledger { @apply rounded-2xl border border-slate-200 bg-white overflow-hidden; }
.feature-ledger > div { @apply grid grid-cols-[2.3rem_1fr] gap-4 px-5 py-4 border-b border-slate-100; }
.feature-ledger__count { @apply w-8 h-8 rounded-full bg-teal-50 grid place-items-center font-mono text-xs font-semibold text-teal-800; }
.feature-ledger strong { @apply text-sm font-semibold text-ink-950; }
.feature-ledger p { @apply mt-1 text-xs leading-relaxed text-slate-500; }
.feature-ledger footer { @apply flex items-center justify-between px-5 py-4 bg-ink-950 text-white; }
.feature-ledger footer span { @apply font-mono text-[10px] uppercase tracking-[.12em] text-slate-400; }
.feature-ledger footer strong { @apply text-xl text-white tabular-nums; }
</style>
