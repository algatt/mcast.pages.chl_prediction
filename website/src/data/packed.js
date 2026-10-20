// Maps packed by the page-data scripts: one byte per pixel, 0–254 spread over
// a fixed range, 255 = no value, base64-encoded, rows south to north.
export function unpack(packed, rows, cols) {
  const bytes = Uint8Array.from(atob(packed.data), (ch) => ch.charCodeAt(0))
  const [lo, hi] = packed.range
  const grid = []
  for (let r = 0; r < rows; r++) {
    const row = new Array(cols)
    for (let c = 0; c < cols; c++) {
      const b = bytes[r * cols + c]
      row[c] = b === 255 ? null : lo + (b / 254) * (hi - lo)
    }
    grid.push(row)
  }
  return grid
}
