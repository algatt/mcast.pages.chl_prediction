import { createRouter, createWebHashHistory } from 'vue-router'

// HashHistory is deliberate: works on any host without server-side rewriting
// (GitHub Pages project pages have no rewrite support, so BrowserHistory
// would 404 on refresh at any non-root route).

const routes = [
  { path: '/',              name: 'home',          component: () => import('./pages/Home.vue') },
  { path: '/primer',        name: 'primer',        component: () => import('./pages/Primer.vue') },
  { path: '/methodology',   name: 'methodology',   component: () => import('./pages/Methodology.vue') },
  { path: '/data',          name: 'data',          component: () => import('./pages/Data.vue') },
  { path: '/forecast',      name: 'forecast',      component: () => import('./pages/Forecast.vue') },
  { path: '/findings/l3-vs-l4',        name: 'l3-vs-l4',        component: () => import('./pages/FindingL3.vue') },
  { path: '/findings/group-ablation',  name: 'group-ablation',  component: () => import('./pages/FindingAblation.vue') },
  { path: '/findings/walk-forward',    name: 'walk-forward',    component: () => import('./pages/FindingWalkForward.vue') },
  { path: '/findings/bloom-detection', name: 'bloom-detection', component: () => import('./pages/FindingBloom.vue') },
  { path: '/glossary',      name: 'glossary',      component: () => import('./pages/Glossary.vue') },
  { path: '/about',         name: 'about',         component: () => import('./pages/About.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

export default createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior() { return { top: 0 } },
})
