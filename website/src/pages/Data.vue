<script setup>
import SectionHeader from '../components/SectionHeader.vue'
import CoverageChart from '../components/CoverageChart.vue'
import FigureCard from '../components/FigureCard.vue'
import ExplainerBox from '../components/ExplainerBox.vue'
import Term from '../components/Term.vue'

const target = {
  name: 'Chlorophyll-a (target)',
  product: 'cmems_obs-oc_med_bgc-plankton_my_l3-multi-1km_P1D',
  source: 'CMEMS',
  res: '1 km × daily',
  years: '1997–present',
  vars: ['CHL'],
  why: 'Multi-sensor L3 merge maximises daily coverage without gap-filling. 25–40% NaN per day is the whole point — see Finding 01.',
}

const predictors = [
  { name: 'SST',                product: 'cmems_SST_MED_SST_L4_REP_OBSERVATIONS_010_021', source: 'CMEMS', res: '~5 km × daily',  years: '1982–', vars: ['analysed_sst'] },
  { name: 'Bathymetry',         product: 'ETOPO 2022 15s',                                 source: 'NOAA (ERDDAP)', res: '~460 m',    years: 'static', vars: ['z'] },
  { name: 'Wind (u10, v10)',    product: 'reanalysis-era5-single-levels',                  source: 'ECMWF (CDS)',   res: '~31 km × noon-daily', years: '1940–', vars: ['u10', 'v10'] },
  { name: 'Salinity',           product: 'cmems_mod_med_phy-sal_my_4.2km_P1D-m',           source: 'CMEMS',         res: '~4 km × daily', years: '1987–', vars: ['so'] },
  { name: 'Currents',           product: 'cmems_mod_med_phy-cur_my_4.2km_P1D-m',           source: 'CMEMS',         res: '~4 km × daily', years: '1987–', vars: ['uo', 'vo'] },
  { name: 'Sea-surface height', product: 'cmems_mod_med_phy-ssh_my_4.2km_P1D-m',           source: 'CMEMS',         res: '~4 km × daily', years: '1987–', vars: ['zos'] },
  { name: 'Mixed-layer depth',  product: 'cmems_mod_med_phy-mld_my_4.2km_P1D-m',           source: 'CMEMS',         res: '~4 km × daily', years: '1987–', vars: ['mlotst'] },
  { name: 'KD490 (light)',      product: 'cmems_obs-oc_med_bgc-transp_my_l3-multi-1km_P1D', source: 'CMEMS',        res: '1 km × daily', years: '1997–', vars: ['KD490'] },
]
</script>

<template>
  <div class="container-page py-12 md:py-16">
    <SectionHeader
      eyebrow="Data sources"
      title="Every dataset, every ID"
      lead="One target, eight predictor groups. Everything regridded onto the 1 km CHL grid. The rule: only the target must be L3; predictors are allowed to be gap-free reanalysis fields."
    />

    <!-- Prime the reader on L3 vs L4 -->
    <ExplainerBox title="Wait — what does 'L3' actually mean?" tone="primer" :open="true">
      <p>
        Satellite data comes in <strong>processing levels</strong>. Think of it as a raw-to-polished spectrum:
      </p>
      <ul>
        <li><strong>Level 1</strong>: raw sensor readings, per satellite pass, in the satellite's own coordinate system. Barely usable unless you are a satellite engineer.</li>
        <li><strong>Level 2</strong>: readings turned into a scientific quantity (e.g. chlorophyll), still per pass, still in swath geometry.</li>
        <li><Term slug="l3"><strong>Level 3</strong></Term> — <span class="badge badge-info ml-1">what we use as target</span> — level-2 data <em>gridded</em> onto a regular map (say 1 km × 1 km) and <em>merged over a day</em>. Cloudy pixels are left <strong>missing</strong>. This is the honest, gappy version.</li>
        <li><Term slug="l4"><strong>Level 4</strong></Term> — <span class="badge badge-warn ml-1">what most others use</span> — level-3 with the gaps <em>filled in</em> by an algorithm like <Term slug="dineof">DINEOF</Term>. Looks clean, but about half of every map is invented rather than observed.</li>
      </ul>
      <p>
        Our target must be L3 so the model is trained on real observations only. Our predictors (SST, wind, currents, etc.) are allowed to be L4 or <Term slug="reanalysis">reanalysis</Term> — they are inputs, not the score, so smoothness is fine.
      </p>
    </ExplainerBox>

    <!-- Region -->
    <div class="card mb-8 grid md:grid-cols-3 gap-6">
      <div class="md:col-span-2">
        <div class="text-xs uppercase tracking-wide font-semibold text-ocean-600 mb-2">Region</div>
        <h3 class="text-xl font-bold text-slate-900 mb-2">Malta–Sicily Channel</h3>
        <p class="text-slate-700 leading-relaxed">
          A 3.5 × 2 degree box in the central Mediterranean covering the Malta plateau, the Sicilian shelf,
          and the deep Strait of Sicily. Three regimes packed into one 280 × 220 km area: shelf (Sicilian
          coast, coastal upwelling), frontal (Atlantic-Ionian Stream), and open-basin (Ionian abyssal water).
        </p>
        <ul class="mt-4 grid grid-cols-2 gap-2 text-sm">
          <li class="flex justify-between"><span class="text-slate-500">Latitude</span> <span class="font-mono">35.5°N – 37.5°N</span></li>
          <li class="flex justify-between"><span class="text-slate-500">Longitude</span> <span class="font-mono">12.0°E – 15.5°E</span></li>
          <li class="flex justify-between"><span class="text-slate-500">Period</span> <span class="font-mono">2021-01 – 2023-12</span></li>
          <li class="flex justify-between"><span class="text-slate-500">Target grid</span> <span class="font-mono">225 × 390 × 1095</span></li>
        </ul>
      </div>
      <div class="flex items-center justify-center">
        <img :src="'figs/02_coverage_map.png'" alt="Per-pixel coverage" class="rounded-lg border border-slate-200 max-w-full h-auto" />
      </div>
    </div>

    <!-- Target -->
    <div class="mb-10">
      <h2 class="text-2xl font-bold text-slate-900 mb-4">Target — chlorophyll-a</h2>
      <div class="card">
        <div class="grid md:grid-cols-3 gap-6">
          <div class="md:col-span-2">
            <h3 class="text-lg font-bold text-slate-900 mb-1">{{ target.name }}</h3>
            <code class="text-xs text-slate-500 font-mono block mb-3">{{ target.product }}</code>
            <p class="text-slate-700 leading-relaxed">{{ target.why }}</p>
            <div class="grid grid-cols-3 gap-2 mt-4 text-sm">
              <div>
                <div class="text-xs text-slate-500 uppercase tracking-wide">Source</div>
                <div class="font-semibold text-slate-800">{{ target.source }}</div>
              </div>
              <div>
                <div class="text-xs text-slate-500 uppercase tracking-wide">Resolution</div>
                <div class="font-semibold text-slate-800">{{ target.res }}</div>
              </div>
              <div>
                <div class="text-xs text-slate-500 uppercase tracking-wide">Coverage</div>
                <div class="font-semibold text-slate-800">{{ target.years }}</div>
              </div>
            </div>
          </div>
          <div>
            <img :src="'figs/01_chl_sample_day.png'" alt="Sample day" class="rounded-lg border border-slate-200 w-full h-auto" />
          </div>
        </div>
      </div>
    </div>

    <!-- Predictors -->
    <div class="mb-10">
      <h2 class="text-2xl font-bold text-slate-900 mb-4">Predictors — 8 groups</h2>
      <div class="grid md:grid-cols-2 gap-4">
        <div v-for="p in predictors" :key="p.name" class="card">
          <h3 class="font-bold text-slate-900 mb-1">{{ p.name }}</h3>
          <code class="text-xs text-slate-500 font-mono block mb-3 break-all">{{ p.product }}</code>
          <div class="grid grid-cols-3 gap-2 text-xs">
            <div>
              <div class="text-slate-500 uppercase tracking-wide font-semibold">Source</div>
              <div class="font-semibold text-slate-800">{{ p.source }}</div>
            </div>
            <div>
              <div class="text-slate-500 uppercase tracking-wide font-semibold">Resolution</div>
              <div class="font-semibold text-slate-800">{{ p.res }}</div>
            </div>
            <div>
              <div class="text-slate-500 uppercase tracking-wide font-semibold">Years</div>
              <div class="font-semibold text-slate-800">{{ p.years }}</div>
            </div>
          </div>
          <div class="mt-2 text-xs text-slate-500">
            Variables: <span class="font-mono text-slate-700">{{ p.vars.join(', ') }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Coverage atlas -->
    <div class="card mb-10">
      <h2 class="text-lg font-bold text-slate-900 mb-1">The coverage atlas — how cloudy is each month?</h2>
      <p class="text-sm text-slate-600 mb-4 leading-relaxed">
        For each day, the fraction of pixels with valid CHL (non-NaN). Averaged per calendar month. Winter (Dec, Jan, Feb) is
        the cloudiest — and, crucially, still above the 25% threshold below which daily forecasting would be untenable. This is
        Gate 2's <em>decision branch</em>: DJF ≥ 25% → daily target. DJF < 25% → 3-day composite. Result: DJF = 43.5%.
      </p>
      <CoverageChart />
    </div>

    <!-- Deliberate omissions -->
    <div class="card bg-slate-50 border-slate-200 mb-10">
      <h2 class="text-lg font-bold text-slate-900 mb-3">Deliberately omitted</h2>
      <ul class="space-y-2 text-slate-700 text-sm leading-relaxed">
        <li><strong>Waves</strong> — only hourly product exists; aggregating to daily was a ~1.7 GB download for marginal expected lift. Deferred until ablation demanded it.</li>
        <li><strong>PAR</strong> — no multi-year L3 PAR product in the Med catalogue. Could be derived from ERA5 solar radiation later.</li>
        <li><strong>BGC nutrients</strong> — optional; marginal value at H+1–H+7 leads is small. The model's own chl-a output would be circular and is refused on principle.</li>
        <li><strong>ASCAT wind</strong> — coastal blind zone in the Maltese strip; ERA5 is the workhorse for now.</li>
      </ul>
    </div>

    <div class="mt-10 flex flex-wrap gap-3 justify-between">
      <router-link to="/methodology" class="px-5 py-2.5 rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors">
        ← Methodology
      </router-link>
      <router-link to="/findings/l3-vs-l4" class="px-5 py-2.5 rounded-lg bg-ocean-600 text-white font-semibold hover:bg-ocean-700 transition-colors">
        Finding 01 →
      </router-link>
    </div>
  </div>
</template>
