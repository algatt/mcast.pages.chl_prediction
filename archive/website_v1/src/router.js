import { createRouter, createWebHashHistory } from 'vue-router'

const siteTitle = 'Observed Ocean'
const siteDescription = 'Reviewer-facing evidence for a 2021–2023 chlorophyll forecasting pipeline in the Malta–Sicily Channel.'

const routes = [
  { path: '/', name: 'home', component: () => import('./pages/Home.vue'), meta: { title: 'Overview' } },
  { path: '/primer', name: 'primer', component: () => import('./pages/Primer.vue'), meta: { title: 'Plain-language primer' } },
  { path: '/methodology', name: 'methodology', component: () => import('./pages/Methodology.vue'), meta: { title: '13-stage pipeline' } },
  { path: '/data', name: 'data', component: () => import('./pages/Data.vue'), meta: { title: 'Data and evidence' } },
  { path: '/forecast', name: 'forecast', component: () => import('./pages/Forecast.vue'), meta: { title: 'Visual diagnostics' } },
  { path: '/findings/observation-contract', name: 'observation-contract', component: () => import('./pages/FindingL3.vue'), meta: { title: 'Observation contract' } },
  { path: '/findings/l3-vs-l4', redirect: '/findings/observation-contract' },
  { path: '/findings/group-ablation', name: 'group-ablation', component: () => import('./pages/FindingAblation.vue'), meta: { title: 'Feature evidence' } },
  { path: '/findings/walk-forward', name: 'walk-forward', component: () => import('./pages/FindingWalkForward.vue'), meta: { title: 'Temporal robustness' } },
  { path: '/findings/bloom-detection', name: 'bloom-detection', component: () => import('./pages/FindingBloom.vue'), meta: { title: 'Bloom-event evidence' } },
  { path: '/glossary', name: 'glossary', component: () => import('./pages/Glossary.vue'), meta: { title: 'Glossary' } },
  { path: '/about', name: 'about', component: () => import('./pages/About.vue'), meta: { title: 'Limitations and reproducibility' } },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior() { return { top: 0 } },
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · ${siteTitle}` : siteTitle
  const description = document.querySelector('meta[name="description"]')
  if (description) description.setAttribute('content', siteDescription)
})

export default router

