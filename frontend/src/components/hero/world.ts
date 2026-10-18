// Coarse continent outlines ([lon, lat] degrees). Dot density hides the roughness; this is a
// stylised dot-matrix globe, not a cartographic source.
export type Poly = [number, number][]

export const LAND: Poly[] = [
  // North America
  [[-166, 68], [-156, 71], [-141, 70], [-125, 70], [-108, 70], [-95, 72], [-85, 69], [-80, 63], [-93, 60], [-94, 57], [-88, 56], [-82, 53], [-79, 56], [-77, 60], [-72, 61], [-65, 60], [-62, 56], [-56, 52], [-60, 47], [-66, 45], [-70, 42], [-74, 40], [-76, 35], [-81, 31], [-80, 26], [-83, 29], [-89, 30], [-94, 29], [-97, 26], [-97, 22], [-94, 18], [-90, 21], [-87, 21], [-88, 16], [-84, 15], [-83, 10], [-80, 8], [-78, 8], [-83, 8], [-86, 11], [-92, 15], [-97, 16], [-105, 20], [-110, 24], [-113, 31], [-110, 23], [-115, 30], [-117, 32], [-121, 35], [-124, 40], [-124, 47], [-128, 51], [-134, 57], [-140, 60], [-148, 60], [-153, 57], [-158, 57], [-164, 60], [-166, 64]],
  // Greenland
  [[-73, 78], [-60, 82], [-30, 83], [-20, 80], [-20, 72], [-25, 68], [-40, 62], [-48, 61], [-52, 66], [-58, 75]],
  // Cuba / Hispaniola-ish
  [[-85, 22], [-77, 22], [-74, 20], [-78, 20], [-82, 22]],
  // South America
  [[-80, 9], [-75, 11], [-70, 12], [-62, 10], [-52, 5], [-50, 0], [-44, -2], [-35, -6], [-38, -13], [-40, -20], [-48, -26], [-53, -34], [-58, -38], [-63, -41], [-65, -46], [-68, -52], [-70, -55], [-74, -52], [-74, -45], [-73, -38], [-71, -30], [-70, -20], [-76, -14], [-81, -6], [-80, -2], [-78, 2], [-77, 8]],
  // Iceland
  [[-24, 64], [-14, 64], [-15, 66], [-22, 66]],
  // British Isles
  [[-5, 50], [1, 51], [2, 53], [-2, 56], [-2, 58], [-6, 58], [-5, 55], [-3, 54], [-5, 52]],
  [[-10, 52], [-6, 52], [-6, 55], [-9, 54]],
  // Scandinavia
  [[5, 59], [5, 62], [10, 64], [15, 68], [21, 70], [28, 71], [30, 69], [28, 66], [25, 65], [21, 63], [17, 61], [19, 60], [16, 56], [13, 55], [11, 59], [8, 58]],
  // Eurasia
  [[-9, 37], [-9, 43], [-2, 44], [-1, 47], [-4, 48], [2, 51], [8, 54], [14, 54], [21, 55], [25, 59], [30, 60], [32, 66], [40, 67], [44, 68], [55, 69], [68, 70], [80, 73], [95, 77], [110, 77], [130, 72], [150, 71], [170, 70], [180, 68], [180, 64], [165, 60], [160, 55], [156, 51], [142, 52], [140, 48], [135, 43], [129, 41], [127, 38], [129, 35], [126, 35], [125, 39], [121, 40], [122, 37], [119, 35], [121, 31], [122, 29], [118, 24], [111, 21], [108, 21], [106, 18], [109, 12], [105, 9], [101, 13], [100, 9], [103, 2], [100, 6], [98, 10], [98, 16], [94, 17], [92, 22], [88, 22], [86, 20], [80, 15], [80, 10], [77, 8], [73, 16], [72, 21], [67, 24], [62, 25], [57, 26], [56, 24], [59, 22], [55, 17], [45, 13], [43, 15], [39, 21], [35, 28], [34, 31], [36, 36], [30, 36], [27, 37], [26, 40], [23, 40], [22, 37], [19, 41], [13, 46], [12, 44], [16, 41], [18, 40], [16, 38], [15, 40], [11, 43], [8, 44], [3, 43], [0, 39], [-2, 37], [-6, 36]],
  // Japan
  [[130, 32], [135, 34], [140, 35], [142, 40], [141, 44], [144, 43], [141, 38], [137, 33]],
  // Borneo / Sumatra
  [[109, 2], [117, 7], [119, 1], [116, -4], [110, -3]],
  [[95, 5], [106, -6], [102, -4], [97, 2]],
  // Africa
  [[-17, 21], [-13, 28], [-6, 36], [10, 37], [11, 33], [20, 31], [25, 32], [32, 31], [34, 28], [38, 20], [43, 12], [51, 12], [48, 5], [41, -2], [40, -10], [41, -16], [35, -24], [33, -28], [27, -34], [20, -35], [17, -30], [12, -17], [14, -9], [9, -1], [9, 4], [5, 5], [-2, 5], [-8, 4], [-13, 8], [-17, 14]],
  // Madagascar
  [[44, -25], [47, -25], [50, -15], [49, -12], [44, -17]],
  // Australia
  [[113, -22], [114, -34], [118, -35], [124, -33], [131, -31], [138, -35], [145, -39], [150, -37], [153, -28], [153, -25], [146, -19], [142, -11], [137, -12], [130, -12], [126, -14], [122, -17]],
  // New Zealand
  [[172, -34], [178, -38], [175, -42], [172, -41]],
  [[167, -46], [174, -41], [172, -44]],
]

export function inPoly(lon: number, lat: number, poly: Poly): boolean {
  let inside = false
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i]
    const [xj, yj] = poly[j]
    if (yi > lat !== yj > lat && lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) inside = !inside
  }
  return inside
}

/** Evenly spaced (by surface area) land dots. */
export function buildLandDots(stepDeg = 2.1): [number, number][] {
  const dots: [number, number][] = []
  for (let lat = -78; lat <= 82; lat += stepDeg) {
    const lonStep = stepDeg / Math.max(0.22, Math.cos((lat * Math.PI) / 180))
    for (let lon = -180; lon < 180; lon += lonStep) {
      if (LAND.some((p) => inPoly(lon, lat, p))) dots.push([lon, lat])
    }
  }
  return dots
}

export interface Region {
  id: string
  city: string
  lat: number
  lon: number
  zones: string
  /** label offset from the node, tuned so European clusters don't collide */
  dx: number
  dy: number
  accent?: boolean
}

// Google Cloud regions used as nodes. Mumbai is highlighted: it is where this deployment lives.
export const REGIONS: Region[] = [
  { id: 'us-central1', city: 'Iowa', lat: 41.26, lon: -95.86, zones: '04', dx: 6, dy: -64 },
  { id: 'us-east4', city: 'N Virginia', lat: 39.04, lon: -77.49, zones: '03', dx: 22, dy: -44 },
  { id: 'us-east1', city: 'S Carolina', lat: 33.2, lon: -80.0, zones: '03', dx: -128, dy: 12 },
  { id: 'northamerica-northeast1', city: 'Montreal', lat: 45.5, lon: -73.6, zones: '03', dx: -34, dy: -72 },
  { id: 'europe-west2', city: 'London', lat: 51.5, lon: -0.12, zones: '03', dx: -20, dy: -70 },
  { id: 'europe-west4', city: 'Netherlands', lat: 53.44, lon: 6.84, zones: '02', dx: -14, dy: -120 },
  { id: 'europe-west3', city: 'Frankfurt', lat: 50.11, lon: 8.68, zones: '03', dx: 18, dy: -94 },
  { id: 'europe-west1', city: 'Belgium', lat: 50.45, lon: 3.82, zones: '03', dx: 40, dy: -46 },
  { id: 'asia-south1', city: 'Mumbai', lat: 19.08, lon: 72.88, zones: '03', dx: 14, dy: -50, accent: true },
  { id: 'asia-south2', city: 'Delhi', lat: 28.61, lon: 77.21, zones: '03', dx: 18, dy: -60 },
  { id: 'asia-southeast1', city: 'Singapore', lat: 1.35, lon: 103.82, zones: '03', dx: 16, dy: -46 },
  { id: 'asia-northeast1', city: 'Tokyo', lat: 35.68, lon: 139.69, zones: '03', dx: 14, dy: -56 },
  { id: 'australia-southeast1', city: 'Sydney', lat: -33.87, lon: 151.21, zones: '03', dx: 12, dy: -46 },
  { id: 'southamerica-east1', city: 'São Paulo', lat: -23.55, lon: -46.63, zones: '03', dx: 12, dy: -46 },
]

export const ARCS: [string, string][] = [
  ['us-central1', 'us-east4'],
  ['us-east1', 'europe-west2'],
  ['us-east4', 'europe-west1'],
  ['northamerica-northeast1', 'europe-west2'],
  ['us-central1', 'europe-west3'],
  ['europe-west2', 'europe-west3'],
  ['europe-west4', 'asia-south1'],
  ['europe-west3', 'asia-south1'],
  ['asia-south1', 'asia-south2'],
  ['asia-south1', 'asia-southeast1'],
  ['asia-southeast1', 'australia-southeast1'],
  ['asia-northeast1', 'us-central1'],
  ['us-east1', 'southamerica-east1'],
  ['southamerica-east1', 'europe-west1'],
]
