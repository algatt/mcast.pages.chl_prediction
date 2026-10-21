import { createRouter, createWebHashHistory } from 'vue-router'
import { steps, stepPath } from './data/steps.js'

const siteTitle = 'Observed Ocean'

const pages = {
  '01': () => import('./pages/Step01.vue'),
  '02': () => import('./pages/Step02.vue'),
  '03': () => import('./pages/Step03.vue'),
  '04': () => import('./pages/Step04.vue'),
  '05': () => import('./pages/Step05.vue'),
  '06': () => import('./pages/Step06.vue'),
  '07': () => import('./pages/Step07.vue'),
  '08': () => import('./pages/Step08.vue'),
  '09': () => import('./pages/Step09.vue'),
  '10': () => import('./pages/Step10.vue'),
}

const routes = [
  { path: '/', name: 'home', component: () => import('./pages/Home.vue') },
  ...steps
    .filter((s) => s.ready)
    .map((s) => ({
      path: stepPath(s),
      name: `step-${s.number}`,
      component: pages[s.number],
      meta: { title: `Step ${s.number} · ${s.title}` },
    })),
  // Earlier addresses used "notebooks".
  { path: '/notebooks/:slug', redirect: (to) => `/steps/${to.params.slug}` },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior(to) {
    if (to.hash) return { el: to.hash, top: 88 }
    return { top: 0 }
  },
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · ${siteTitle}` : siteTitle
})

export default router
