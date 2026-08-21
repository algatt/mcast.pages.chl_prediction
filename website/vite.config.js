import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// For GitHub Pages project pages, set `base` to '/<repo-name>/'.
// If deploying at the repo root or a custom domain, use '/' or './'.
// We use './' so assets resolve relative to the HTML wherever it's hosted;
// vue-router HashHistory (see src/router.js) then handles the client-side routes.
export default defineConfig({
  base: './',
  plugins: [vue()],
  server: { port: 5173, open: false },
})
