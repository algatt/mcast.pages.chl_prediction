<template>
  <footer class="mt-20 border-t border-slate-200 bg-[#07171e] text-slate-300">
    <div class="container-page py-10 grid gap-8 md:grid-cols-[1fr_auto] md:items-end">
      <div>
        <div class="label-caps !text-cyan-200">Observed Ocean</div>
        <p class="mt-2 max-w-xl text-sm leading-relaxed text-slate-400">
          A reviewer-facing companion to a 13-notebook chlorophyll forecasting pipeline for the Malta–Sicily Channel. Results cover 2021–2023 and are research evidence, not an operational warning service.
        </p>
      </div>
      <div class="flex flex-wrap gap-x-5 gap-y-2 text-sm">
        <router-link to="/methodology" class="hover:text-white">Pipeline</router-link>
        <router-link to="/data" class="hover:text-white">Evidence</router-link>
        <router-link to="/about" class="hover:text-white">Limitations</router-link>
        <router-link to="/glossary" class="hover:text-white">Glossary</router-link>
      </div>
    </div>
  </footer>
</template>

