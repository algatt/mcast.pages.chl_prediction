<script setup>
import { computed, onMounted, ref, watch } from 'vue'

// A map of one or more fields on the 1 km chlorophyll grid, drawn cell by cell
// on a canvas, with a hover read-out. Row 0 of every field is the southernmost.
//
// Each layer is either
//   sequential:  { values, decode, ramp, domain, log?, ticks, tickFormat?, legendTitle,
//                  format, missingLabel?, nativeGrid? }
//   categorical: { categoryAt(r, c), categories: { key: { color, label } } }
// and may supply describe(r, c) -> { line, note } to customise the read-out.
const props = defineProps({
  latitude: { type: Array, required: true },
  longitude: { type: Array, required: true },
  sea: { type: Array, required: true },
  layers: { type: Array, required: true },
  ariaLabel: { type: String, required: true },
  // Optional v-model for the selected layer, so a page can keep the choice
  // when it swaps the layers.
  modelValue: { type: String, default: null },
})
const emit = defineEmits(['update:modelValue'])

const lat = props.latitude
const lon = props.longitude
const rows = lat.length
const cols = lon.length

// Grid cells are not square on the ground: 1° of longitude is cos(latitude)
// times as long as 1° of latitude.
const meanLat = (lat[0] + lat[rows - 1]) / 2
const dLat = (lat[rows - 1] - lat[0]) / (rows - 1)
const dLon = (lon[cols - 1] - lon[0]) / (cols - 1)
const CELL_W = 6
const CELL_H = (CELL_W * dLat) / (dLon * Math.cos((meanLat * Math.PI) / 180))
const width = cols * CELL_W
const height = Math.round(rows * CELL_H)

const COLORS = { gap: '#eeede8', gapHatch: '#d3d1c9', land: '#a9a69d' }

const activeId = ref(props.layers.some((l) => l.id === props.modelValue) ? props.modelValue : props.layers[0].id)
watch(activeId, (id) => emit('update:modelValue', id))
const layer = computed(() => props.layers.find((l) => l.id === activeId.value))
const showGrid = ref(false)

function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}

const position = (l, value) => {
  const v = l.log ? Math.log10(value) : value
  const [a, b] = l.log ? l.domain.map(Math.log10) : l.domain
  return Math.min(1, Math.max(0, (v - a) / (b - a)))
}

function rampColor(l, value) {
  const stops = l._rgb || (l._rgb = l.ramp.map(hexToRgb))
  const x = position(l, value) * (stops.length - 1)
  const i = Math.min(stops.length - 2, Math.floor(x))
  const f = x - i
  const c = stops[i].map((v, k) => Math.round(v + (stops[i + 1][k] - v) * f))
  return `rgb(${c[0]},${c[1]},${c[2]})`
}

const canvas = ref(null)
let hatch = null

function makeHatch(ctx) {
  const tile = document.createElement('canvas')
  tile.width = 6
  tile.height = 6
  const t = tile.getContext('2d')
  t.fillStyle = COLORS.gap
  t.fillRect(0, 0, 6, 6)
  t.strokeStyle = COLORS.gapHatch
  t.beginPath()
  t.moveTo(0, 6)
  t.lineTo(6, 0)
  t.stroke()
  return ctx.createPattern(tile, 'repeat')
}

function cellFill(l, r, c) {
  if (!props.sea[r][c]) return COLORS.land
  if (l.kind === 'categorical') {
    const key = l.categoryAt(r, c)
    return key === null ? hatch : l.categories[key].color
  }
  const raw = l.values[r][c]
  return raw === null ? hatch : rampColor(l, l.decode(raw))
}

// Native cell edges sit halfway between neighbouring cell centres.
function edges(centres) {
  const e = []
  for (let i = 0; i < centres.length - 1; i++) e.push((centres[i] + centres[i + 1]) / 2)
  const step = centres[1] - centres[0]
  return [centres[0] - step / 2, ...e, centres[centres.length - 1] + step / 2]
}
const yOf = (latitude) => ((lat[rows - 1] + dLat / 2 - latitude) / dLat) * CELL_H
const xOf = (longitude) => ((longitude - (lon[0] - dLon / 2)) / dLon) * CELL_W

function draw() {
  const ctx = canvas.value.getContext('2d')
  if (!hatch) hatch = makeHatch(ctx)
  const l = layer.value
  ctx.clearRect(0, 0, width, height)
  for (let r = 0; r < rows; r++) {
    const y0 = Math.round((rows - 1 - r) * CELL_H)
    const y1 = Math.round((rows - r) * CELL_H)
    for (let c = 0; c < cols; c++) {
      ctx.fillStyle = cellFill(l, r, c)
      ctx.fillRect(c * CELL_W, y0, CELL_W, y1 - y0)
    }
  }
  if (showGrid.value && l.nativeGrid) {
    // Snap each native edge to the nearest 1 km pixel boundary: that is where
    // the copied values actually change on this grid.
    ctx.strokeStyle = 'rgba(7, 23, 30, 0.55)'
    ctx.lineWidth = 1
    ctx.beginPath()
    for (const la of edges(l.nativeGrid.latitude)) {
      const y = Math.round(Math.round(yOf(la) / CELL_H) * CELL_H) + 0.5
      if (y > 0 && y < height) { ctx.moveTo(0, y); ctx.lineTo(width, y) }
    }
    for (const lo of edges(l.nativeGrid.longitude)) {
      const x = Math.round(xOf(lo) / CELL_W) * CELL_W + 0.5
      if (x > 0 && x < width) { ctx.moveTo(x, 0); ctx.lineTo(x, height) }
    }
    ctx.stroke()
  }
}

onMounted(draw)
watch([activeId, showGrid], draw)

function place(latitude, longitude) {
  return {
    left: `${(100 * xOf(longitude)) / width}%`,
    top: `${(100 * yOf(latitude)) / height}%`,
  }
}
const placeLabels = [
  { name: 'Sicily', ...place(36.84, 14.84), align: 'center' },
  { name: 'Malta', ...place(35.87, 14.6), align: 'left' },
  { name: 'Gozo', ...place(36.07, 14.16), align: 'right' },
]

// Legend ticks, with the end ticks aligned to the bar's edges.
const ticks = computed(() => {
  const l = layer.value
  if (l.kind !== 'sequential') return []
  return l.ticks.map((t, i) => ({
    left: `${100 * position(l, t)}%`,
    label: l.tickFormat ? l.tickFormat(t, i) : `${t}`,
    align: i === 0 ? '' : i === l.ticks.length - 1 ? '-translate-x-full' : '-translate-x-1/2',
  }))
})
const rampCss = computed(() =>
  layer.value.kind === 'sequential' ? `linear-gradient(90deg, ${layer.value.ramp.join(', ')})` : '',
)

const hover = ref(null)

function onMove(event) {
  const rect = canvas.value.getBoundingClientRect()
  const x = ((event.clientX - rect.left) / rect.width) * width
  const y = ((event.clientY - rect.top) / rect.height) * height
  const c = Math.floor(x / CELL_W)
  const r = rows - 1 - Math.floor(y / CELL_H)
  if (c < 0 || c >= cols || r < 0 || r >= rows) {
    hover.value = null
    return
  }
  hover.value = {
    r, c,
    left: event.clientX - rect.left,
    top: event.clientY - rect.top,
    flip: event.clientX - rect.left > rect.width * 0.6,
  }
}

const hoverText = computed(() => {
  if (!hover.value) return null
  const { r, c } = hover.value
  const where = `${lat[r].toFixed(3)}°N, ${lon[c].toFixed(3)}°E`
  const l = layer.value
  if (!props.sea[r][c]) return { where, line: 'Land' }
  if (l.describe) return { where, ...l.describe(r, c) }
  if (l.kind === 'categorical') {
    const key = l.categoryAt(r, c)
    return { where, line: key === null ? 'No value' : l.categories[key].label }
  }
  const raw = l.values[r][c]
  return { where, line: raw === null ? (l.missingLabel || 'No observation') : l.format(l.decode(raw)) }
})
</script>

<template>
  <div>
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="segmented" role="group" aria-label="Map view">
        <button v-for="l in layers" :key="l.id" type="button" :aria-pressed="activeId === l.id" @click="activeId = l.id">
          {{ l.label }}
        </button>
      </div>
      <label v-if="layer.nativeGrid" class="inline-flex items-center gap-2 text-sm text-slate-600 cursor-pointer select-none">
        <input v-model="showGrid" type="checkbox" class="accent-teal-700" />
        Show the original grid
      </label>
    </div>

    <div class="mt-4 grid gap-6 md:grid-cols-[minmax(0,1fr)_14rem] items-start">
      <div class="relative mx-auto w-full max-w-[34rem]">
        <canvas
          ref="canvas"
          :width="width"
          :height="height"
          class="block w-full h-auto rounded-lg border border-slate-200"
          :style="{ aspectRatio: `${width} / ${height}`, imageRendering: 'pixelated' }"
          role="img"
          :aria-label="`${ariaLabel}: ${layer.label}`"
          @mousemove="onMove"
          @mouseleave="hover = null"
        ></canvas>

        <span v-for="p in placeLabels" :key="p.name" class="map-label" :class="`map-label--${p.align}`"
              :style="{ left: p.left, top: p.top }">{{ p.name }}</span>

        <div
          v-if="hover && hoverText"
          class="tooltip"
          :style="{
            left: `${hover.left + (hover.flip ? -14 : 14)}px`,
            top: `${hover.top + 14}px`,
            transform: hover.flip ? 'translateX(-100%)' : 'none',
          }"
        >
          <div class="font-semibold text-ink-950">{{ hoverText.line }}</div>
          <div v-if="hoverText.note" class="text-slate-600">{{ hoverText.note }}</div>
          <div class="mt-0.5 font-mono text-[10px] text-slate-500">{{ hoverText.where }}</div>
        </div>
      </div>

      <div class="text-xs text-slate-600 space-y-4">
        <div v-if="layer.kind === 'sequential'">
          <div class="label-caps">{{ layer.legendTitle }}</div>
          <div class="mt-2 h-3 rounded" :style="{ background: rampCss }"></div>
          <div class="relative mt-1 h-4 font-mono text-[10px] text-slate-500 tabular-nums">
            <span v-for="t in ticks" :key="t.label" class="absolute" :class="t.align" :style="{ left: t.left }">{{ t.label }}</span>
          </div>
          <p v-if="layer.legendNote" class="mt-1 text-[11px] text-slate-500">{{ layer.legendNote }}</p>
        </div>
        <template v-else>
          <div v-for="(cat, key) in layer.categories" :key="key" class="flex items-center gap-2">
            <span class="swatch" :style="{ background: cat.color }"></span>
            {{ cat.label }}
          </div>
        </template>
        <div v-if="layer.showMissing !== false" class="flex items-center gap-2">
          <span class="swatch swatch--gap"></span>
          {{ layer.missingLegend || 'No observation' }}
        </div>
        <div class="flex items-center gap-2">
          <span class="swatch" :style="{ background: COLORS.land }"></span>
          Land
        </div>
        <p class="text-[11px] leading-relaxed text-slate-500">Hover over the map to read individual 1 km pixels.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.map-label {
  position: absolute;
  pointer-events: none;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #0b0b0b;
  text-shadow: 0 0 3px #fff, 0 0 3px #fff, 0 0 2px #fff;
  transform: translateY(-50%);
}
.map-label--center { transform: translate(-50%, -50%); }
.map-label--right { transform: translate(-100%, -50%); }

.swatch {
  @apply inline-block w-4 h-4 rounded-sm border border-black/10 shrink-0;
}
.swatch--gap {
  background: repeating-linear-gradient(135deg, var(--gap-hatch) 0 1px, var(--gap) 1px 5px);
}
</style>
