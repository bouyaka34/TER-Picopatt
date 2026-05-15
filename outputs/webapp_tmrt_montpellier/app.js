const data = window.PICOPATT_DATA;
const heatmap = data.main_heatmap;

const dom = {
  scenarioTitle: document.querySelector("#scenarioTitle"),
  scenarioDate: document.querySelector("#scenarioDate"),
  mapTitle: document.querySelector("#mapTitle"),
  tmrtMin: document.querySelector("#tmrtMin"),
  tmrtMedian: document.querySelector("#tmrtMedian"),
  tmrtMax: document.querySelector("#tmrtMax"),
  observedRows: document.querySelector("#observedRows"),
  gridPoints: document.querySelector("#gridPoints"),
  granularity: document.querySelector("#granularity"),
  scenarioCount: document.querySelector("#scenarioCount"),
  legendMin: document.querySelector("#legendMin"),
  legendMax: document.querySelector("#legendMax"),
  leafletMap: document.querySelector("#leafletMap"),
  loadingLayer: document.querySelector("#loadingLayer"),
  errorLayer: document.querySelector("#errorLayer"),
  zoomOut: document.querySelector("#zoomOut"),
  zoomIn: document.querySelector("#zoomIn"),
  fitView: document.querySelector("#fitView"),
  opacityRange: document.querySelector("#opacityRange"),
  opacityValue: document.querySelector("#opacityValue"),
  tmrtRangeMin: document.querySelector("#tmrtRangeMin"),
  tmrtRangeMax: document.querySelector("#tmrtRangeMax"),
  legendSelection: document.querySelector("#legendSelection"),
  legendRangeLabel: document.querySelector("#legendRangeLabel"),
  routeControls: document.querySelector("#routeControls"),
  routeModeControls: document.querySelector("#routeModeControls"),
  routeNote: document.querySelector("#routeNote"),
};

const INFERNO = [
  [0, 0, 4],
  [8, 5, 29],
  [24, 12, 60],
  [47, 10, 91],
  [70, 11, 110],
  [95, 24, 127],
  [123, 35, 130],
  [152, 45, 128],
  [182, 54, 121],
  [211, 67, 110],
  [235, 87, 96],
  [248, 118, 92],
  [253, 150, 104],
  [254, 183, 126],
  [251, 209, 145],
  [252, 255, 164],
];
const PLAN_TILE_SUBDOMAINS = ["a", "b", "c", "d"];
const SLIDER_STEPS = 1000;
const MIN_RANGE_STEPS = 70;
const FILTER_MARGIN_C = 0.2;

const state = {
  map: null,
  bounds: null,
  heatmapLayer: null,
  routeGroup: null,
  routeRenderer: null,
  routeMode: "trace",
  enabledRoutes: {},
  rangeMin: heatmap.tmrt_min,
  rangeMax: heatmap.tmrt_max,
};
let heatmapRedrawFrame = null;

function fmtNumber(value) {
  return new Intl.NumberFormat("fr-FR").format(value);
}

function fmtTemp(value) {
  if (!Number.isFinite(value)) return "-";
  return `${value.toFixed(1)} \u00b0C`;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function lerp(a, b, t) {
  return a + (b - a) * t;
}

function colorRampRgb(t) {
  const scaled = clamp(t, 0, 1) * (INFERNO.length - 1);
  const idx = Math.min(INFERNO.length - 2, Math.floor(scaled));
  const local = scaled - idx;
  return INFERNO[idx].map((channel, i) => Math.round(lerp(channel, INFERNO[idx + 1][i], local)));
}

function colorRamp(t) {
  const rgb = colorRampRgb(t);
  return `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
}

function valueTileUrl(coords) {
  return (heatmap.value_tile_url_template || heatmap.tile_url_template || heatmap.image_url)
    .replace("{z}", coords.z)
    .replace("{x}", coords.x)
    .replace("{y}", coords.y);
}

function scheduleHeatmapRedraw() {
  if (!state.heatmapLayer) return;
  if (heatmapRedrawFrame) cancelAnimationFrame(heatmapRedrawFrame);
  heatmapRedrawFrame = requestAnimationFrame(() => {
    heatmapRedrawFrame = null;
    state.heatmapLayer.redraw();
  });
}

function createFilteredHeatmapLayer() {
  return L.GridLayer.extend({
    createTile(coords, done) {
      const tile = L.DomUtil.create("canvas", "tmrt-heatmap-tile");
      const size = this.getTileSize();
      tile.width = size.x;
      tile.height = size.y;

      const context = tile.getContext("2d", { willReadFrequently: true });
      const image = new Image();
      image.decoding = "async";
      image.onload = () => {
        context.clearRect(0, 0, size.x, size.y);
        context.drawImage(image, 0, 0, size.x, size.y);

        const pixels = context.getImageData(0, 0, size.x, size.y);
        const buffer = pixels.data;
        const colorMin = Number.isFinite(data.color_vmin) ? data.color_vmin : data.vmin;
        const colorMax = Number.isFinite(data.color_vmax) ? data.color_vmax : data.vmax;
        for (let i = 0; i < buffer.length; i += 4) {
          const alpha = buffer[i + 3];
          if (alpha < 4) {
            buffer[i + 3] = 0;
            continue;
          }
          const value = data.vmin + (buffer[i] / 255) * (data.vmax - data.vmin);
          if (value < state.rangeMin - FILTER_MARGIN_C || value > state.rangeMax + FILTER_MARGIN_C) {
            buffer[i + 3] = 0;
          } else {
            const rgb = colorRampRgb((value - colorMin) / Math.max(colorMax - colorMin, 1e-9));
            buffer[i] = rgb[0];
            buffer[i + 1] = rgb[1];
            buffer[i + 2] = rgb[2];
            buffer[i + 3] = Math.min(255, Math.round(alpha * 0.92));
          }
        }
        context.putImageData(pixels, 0, 0);
        done(null, tile);
      };
      image.onerror = () => {
        context.clearRect(0, 0, size.x, size.y);
        done(null, tile);
      };
      image.src = valueTileUrl(coords);
      return tile;
    },
  });
}

function divergingColor(t) {
  const stops = [
    [33, 102, 172],
    [247, 247, 247],
    [178, 24, 43],
  ];
  const scaled = clamp(t, 0, 1) * 2;
  const idx = Math.min(1, Math.floor(scaled));
  const local = scaled - idx;
  const rgb = stops[idx].map((channel, i) => Math.round(lerp(channel, stops[idx + 1][i], local)));
  return `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
}

function routeValueColor(mode, value) {
  const scales = data.routes?.scale || {};
  const scale = scales[mode] || scales.pred || {};
  const vmin = Number(scale.vmin);
  const vmax = Number(scale.vmax);
  if (!Number.isFinite(value) || !Number.isFinite(vmin) || !Number.isFinite(vmax) || vmax <= vmin) {
    return "#111111";
  }
  if (mode === "error") return divergingColor((value - vmin) / (vmax - vmin));
  return colorRamp((value - vmin) / (vmax - vmin));
}

function routeValueAt(point, mode) {
  if (mode === "observed") return point[3];
  if (mode === "error") return point[4];
  return point[2];
}

function setLoading(isLoading) {
  dom.loadingLayer.classList.toggle("hidden", !isLoading);
}

function showError(show) {
  dom.errorLayer.classList.toggle("hidden", !show);
}

function getRoutes() {
  return data.routes?.items || [];
}

function ensureRouteState() {
  for (const route of getRoutes()) {
    if (!(route.id in state.enabledRoutes)) {
      state.enabledRoutes[route.id] = true;
    }
  }
}

function routeSectionLatLngs(section) {
  return section.points.map(([lon, lat]) => [lat, lon]);
}

function updateRouteNote() {
  const routes = getRoutes();
  const activeCount = routes.filter((route) => state.enabledRoutes[route.id]).length;
  if (!routes.length) {
    dom.routeNote.textContent = "Aucun parcours disponible.";
    return;
  }
  if (state.routeMode === "trace") {
    dom.routeNote.textContent = `${activeCount}/${routes.length} parcours affiches.`;
    return;
  }
  const labelByMode = {
    pred: "Tmrt predite",
    observed: "Tmrt observee",
    error: "Erreur pred. - obs.",
  };
  const scale = data.routes?.scale?.[state.routeMode] || {};
  dom.routeNote.textContent = `${activeCount}/${routes.length} parcours. ${labelByMode[state.routeMode]}: ${fmtTemp(Number(scale.vmin))} - ${fmtTemp(Number(scale.vmax))}.`;
}

function renderRouteControls() {
  ensureRouteState();
  const routes = getRoutes();
  dom.routeControls.innerHTML = "";

  if (!routes.length) {
    dom.routeControls.textContent = "Aucun parcours trouve.";
    updateRouteNote();
    return;
  }

  for (const route of routes) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "route-toggle";
    button.dataset.routeId = route.id;
    button.style.setProperty("--route-color", route.color);
    button.innerHTML = `<span>${route.order}</span><strong>${route.name}</strong>`;
    button.classList.toggle("active", Boolean(state.enabledRoutes[route.id]));
    button.addEventListener("click", () => {
      state.enabledRoutes[route.id] = !state.enabledRoutes[route.id];
      button.classList.toggle("active", Boolean(state.enabledRoutes[route.id]));
      updateRouteNote();
      renderRoutes();
    });
    dom.routeControls.appendChild(button);
  }

  updateRouteNote();
}

function renderRoutes() {
  if (!state.routeGroup) return;

  state.routeGroup.clearLayers();
  const routes = getRoutes().filter((route) => state.enabledRoutes[route.id]);

  for (const route of routes) {
    for (const section of route.sections) {
      if (!section.points || section.points.length < 2) continue;

      if (state.routeMode === "trace") {
        L.polyline(routeSectionLatLngs(section), {
          color: "#ffffff",
          opacity: 0.72,
          pane: "routesPane",
          renderer: state.routeRenderer,
          smoothFactor: 1.25,
          weight: 5.2,
        }).addTo(state.routeGroup);
        L.polyline(routeSectionLatLngs(section), {
          color: route.color,
          opacity: 1,
          pane: "routesPane",
          renderer: state.routeRenderer,
          smoothFactor: 1.25,
          weight: 2.6,
        }).addTo(state.routeGroup);
        continue;
      }

      for (let i = 1; i < section.points.length; i += 1) {
        const [lonA, latA] = section.points[i - 1];
        const [lonB, latB] = section.points[i];
        const valueA = routeValueAt(section.points[i - 1], state.routeMode);
        const valueB = routeValueAt(section.points[i], state.routeMode);
        L.polyline(
          [
            [latA, lonA],
            [latB, lonB],
          ],
          {
            color: routeValueColor(state.routeMode, (valueA + valueB) / 2),
            opacity: 0.98,
            pane: "routesPane",
            renderer: state.routeRenderer,
            smoothFactor: 1,
            weight: 2.15,
          },
        ).addTo(state.routeGroup);
      }
    }
  }
}

function updateDataPanel() {
  dom.scenarioTitle.textContent = "CatBoost - grille 10 m";
  dom.mapTitle.textContent = heatmap.title;
  dom.tmrtMin.textContent = fmtTemp(heatmap.tmrt_min);
  dom.tmrtMedian.textContent = fmtTemp(heatmap.tmrt_median);
  dom.tmrtMax.textContent = fmtTemp(heatmap.tmrt_max);
  dom.observedRows.textContent = fmtNumber(heatmap.n_predicted_points);
  dom.scenarioDate.textContent = `Raster ${heatmap.raster_bins_x} x ${heatmap.raster_bins_y}`;
  dom.gridPoints.textContent = fmtNumber(data.n_grid_points);
  dom.granularity.textContent = `${data.meters_per_pixel} m`;
  dom.scenarioCount.textContent = data.model.includes("CatBoost") ? "CatBoost" : data.model;
  dom.legendMin.textContent = fmtTemp(data.vmin);
  dom.legendMax.textContent = fmtTemp(data.vmax);
}

function sliderToTmrt(value) {
  const t = Number(value) / SLIDER_STEPS;
  return data.vmin + t * (data.vmax - data.vmin);
}

function updateLegendSelection(redraw = true) {
  let low = Number(dom.tmrtRangeMin.value);
  let high = Number(dom.tmrtRangeMax.value);
  if (low > high - MIN_RANGE_STEPS) {
    if (document.activeElement === dom.tmrtRangeMin) {
      low = high - MIN_RANGE_STEPS;
    } else {
      high = low + MIN_RANGE_STEPS;
    }
  }
  low = clamp(low, 0, SLIDER_STEPS - MIN_RANGE_STEPS);
  high = clamp(high, MIN_RANGE_STEPS, SLIDER_STEPS);
  if (low > high - MIN_RANGE_STEPS) low = high - MIN_RANGE_STEPS;
  dom.tmrtRangeMin.value = String(low);
  dom.tmrtRangeMax.value = String(high);

  const left = (low / SLIDER_STEPS) * 100;
  const right = 100 - (high / SLIDER_STEPS) * 100;
  dom.legendSelection.style.left = `${left}%`;
  dom.legendSelection.style.right = `${right}%`;

  state.rangeMin = sliderToTmrt(low);
  state.rangeMax = sliderToTmrt(high);
  dom.legendRangeLabel.textContent = `${fmtTemp(state.rangeMin)} - ${fmtTemp(state.rangeMax)}`;

  if (redraw && state.heatmapLayer) {
    scheduleHeatmapRedraw();
  }
}

function initLeafletMap() {
  if (!window.L) {
    setLoading(false);
    showError(true);
    dom.errorLayer.textContent = "Leaflet indisponible";
    return;
  }

  const [[south, west], [north, east]] = data.bounds;
  state.bounds = L.latLngBounds([south, west], [north, east]);
  state.routeRenderer = L.canvas({ padding: 0.45 });
  state.map = L.map(dom.leafletMap, {
    attributionControl: false,
    maxBounds: state.bounds.pad(0.18),
    maxBoundsViscosity: 0.7,
    maxZoom: 17,
    minZoom: 12,
    preferCanvas: true,
    renderer: state.routeRenderer,
    scrollWheelZoom: true,
    zoomControl: false,
    zoomDelta: 1,
    zoomSnap: 1,
  });

  state.map.createPane("heatmapPane");
  state.map.getPane("heatmapPane").style.zIndex = 420;
  state.map.getPane("heatmapPane").style.opacity = String(Number(dom.opacityRange.value) / 100);
  state.map.getPane("heatmapPane").classList.add("leaflet-heatmap-pane");

  state.map.createPane("routesPane");
  state.map.getPane("routesPane").style.zIndex = 520;

  const satelliteLayer = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
    className: "satellite-tile",
    crossOrigin: true,
    detectRetina: false,
    keepBuffer: 3,
    maxNativeZoom: 19,
    maxZoom: 19,
    tileSize: 256,
    updateWhenIdle: true,
    updateWhenZooming: false,
  }).addTo(state.map);

  satelliteLayer.on("tileerror", (event) => {
    const { x, y, z } = event.coords;
    event.tile.src = `https://tile.openstreetmap.org/${z}/${x}/${y}.png`;
  });

  L.tileLayer("https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}@2x.png", {
    className: "city-label-tile",
    detectRetina: false,
    keepBuffer: 3,
    maxNativeZoom: 20,
    maxZoom: 20,
    opacity: 0.68,
    subdomains: PLAN_TILE_SUBDOMAINS,
    tileSize: 256,
    updateWhenIdle: true,
    updateWhenZooming: false,
  }).addTo(state.map);

  const FilteredHeatmapLayer = createFilteredHeatmapLayer();
  state.heatmapLayer = new FilteredHeatmapLayer({
    bounds: state.bounds,
    keepBuffer: 2,
    maxZoom: heatmap.tile_max_zoom || 17,
    minZoom: heatmap.tile_min_zoom || 12,
    noWrap: true,
    pane: "heatmapPane",
    tileSize: 256,
    updateWhenIdle: true,
    updateWhenZooming: false,
  })
    .once("load", () => {
      setLoading(false);
      showError(false);
    })
    .on("error", () => {
      setLoading(false);
      showError(true);
    })
    .addTo(state.map);

  state.routeGroup = L.layerGroup([], { pane: "routesPane" }).addTo(state.map);
  state.map.fitBounds(state.bounds, { animate: false, padding: [18, 18] });
  renderRoutes();
}

function bindControls() {
  dom.zoomOut.addEventListener("click", () => {
    if (state.map) state.map.zoomOut(1);
  });

  dom.zoomIn.addEventListener("click", () => {
    if (state.map) state.map.zoomIn(1);
  });

  dom.fitView.addEventListener("click", () => {
    if (state.map) state.map.fitBounds(state.bounds, { padding: [18, 18] });
  });

  dom.opacityRange.addEventListener("input", () => {
    const value = Number(dom.opacityRange.value);
    if (state.map) state.map.getPane("heatmapPane").style.opacity = String(value / 100);
    dom.opacityValue.textContent = `${value}%`;
  });

  dom.tmrtRangeMin.addEventListener("input", () => updateLegendSelection(true));
  dom.tmrtRangeMax.addEventListener("input", () => updateLegendSelection(true));

  dom.routeModeControls.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      state.routeMode = button.dataset.routeMode;
      dom.routeModeControls.querySelectorAll("button").forEach((item) => {
        item.classList.toggle("active", item === button);
      });
      updateRouteNote();
      renderRoutes();
    });
  });

  window.addEventListener("resize", () => {
    if (state.map) {
      state.map.invalidateSize();
      state.map.fitBounds(state.bounds, { animate: false, padding: [18, 18] });
    }
  });
}

setLoading(true);
showError(false);
updateDataPanel();
updateLegendSelection(false);
renderRouteControls();
bindControls();
initLeafletMap();
