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
  controlPanel: document.querySelector(".control-panel"),
  panelTabs: document.querySelector("#panelTabs"),
  selectionName: document.querySelector("#selectionName"),
  selectionDrawButton: document.querySelector("#selectionDrawButton"),
  selectionAddButton: document.querySelector("#selectionAddButton"),
  selectionViewportButton: document.querySelector("#selectionViewportButton"),
  selectionClearButton: document.querySelector("#selectionClearButton"),
  selectionRangeLabel: document.querySelector("#selectionRangeLabel"),
  selectionStatus: document.querySelector("#selectionStatus"),
  selectionList: document.querySelector("#selectionList"),
  selectionExportButton: document.querySelector("#selectionExportButton"),
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
  selectionRenderer: null,
  routeMode: "trace",
  enabledRoutes: {},
  rangeMin: heatmap.tmrt_min,
  rangeMax: heatmap.tmrt_max,
  activePanelTab: "map",
  isSelectionDrawing: false,
  selectionStart: null,
  selectionBounds: null,
  selectionRectangle: null,
  selections: [],
  selectionGridValues: null,
  selectionGridPromise: null,
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

function setSelectionStatus(message, tone = "") {
  if (!dom.selectionStatus) return;
  dom.selectionStatus.textContent = message;
  dom.selectionStatus.classList.toggle("ready", tone === "ready");
  dom.selectionStatus.classList.toggle("warning", tone === "warning");
}

function updateSelectionPaneVisibility() {
  if (!state.map) return;
  const pane = state.map.getPane("selectionPane");
  if (pane) pane.style.display = state.activePanelTab === "selection" ? "" : "none";
}

function setActivePanelTab(tab) {
  state.activePanelTab = tab;
  if (tab !== "selection" && state.isSelectionDrawing) {
    setSelectionDrawing(false);
  }
  document.body.classList.toggle("selection-mode", tab === "selection");
  dom.controlPanel.classList.toggle("selection-mode", tab === "selection");
  dom.panelTabs.querySelectorAll("button").forEach((button) => {
    button.classList.toggle("active", button.dataset.panelTab === tab);
  });
  updateSelectionPaneVisibility();
  scheduleHeatmapRedraw();
  if (state.map) {
    requestAnimationFrame(() => state.map.invalidateSize());
  }
}

function setSelectionLoading(isLoading) {
  dom.selectionAddButton.disabled = isLoading;
  dom.selectionViewportButton.disabled = isLoading;
  dom.selectionExportButton.disabled = isLoading || state.selections.length === 0;
}

function renderSelectionList() {
  dom.selectionList.innerHTML = "";
  dom.selectionExportButton.disabled = state.selections.length === 0;

  if (!state.selections.length) {
    const empty = document.createElement("p");
    empty.className = "selection-empty";
    empty.textContent = "Aucune zone exportable";
    dom.selectionList.appendChild(empty);
    return;
  }

  for (const selection of state.selections) {
    const item = document.createElement("div");
    item.className = "selection-item";

    const title = document.createElement("strong");
    title.textContent = selection.label;

    const detail = document.createElement("span");
    detail.textContent = `${fmtNumber(selection.points.length)} pts | moy. ${fmtTemp(selection.mean)} | ${fmtTemp(selection.min)} - ${fmtTemp(selection.max)}`;

    const button = document.createElement("button");
    button.type = "button";
    button.dataset.selectionId = selection.id;
    button.textContent = "x";
    button.title = "Retirer";

    item.appendChild(title);
    item.appendChild(detail);
    item.appendChild(button);
    dom.selectionList.appendChild(item);
  }
}

async function loadSelectionGrid() {
  if (state.selectionGridValues) return state.selectionGridValues;
  if (!data.selection_grid?.url) {
    throw new Error("Selection grid is missing.");
  }
  if (!state.selectionGridPromise) {
    state.selectionGridPromise = fetch(data.selection_grid.url)
      .then((response) => {
        if (!response.ok) throw new Error(`Selection grid fetch failed: ${response.status}`);
        return response.arrayBuffer();
      })
      .then((buffer) => {
        const values = new Float32Array(buffer);
        const expectedLength = Number(data.selection_grid.rows) * Number(data.selection_grid.cols);
        if (values.length !== expectedLength) {
          throw new Error(`Unexpected selection grid length: ${values.length}`);
        }
        state.selectionGridValues = values;
        return values;
      });
  }
  return state.selectionGridPromise;
}

function clampSelectionBounds(bounds) {
  const [[south, west], [north, east]] = data.selection_grid?.bounds || data.bounds;
  const clampedSouth = clamp(bounds.getSouth(), south, north);
  const clampedNorth = clamp(bounds.getNorth(), south, north);
  const clampedWest = clamp(bounds.getWest(), west, east);
  const clampedEast = clamp(bounds.getEast(), west, east);
  if (clampedNorth <= clampedSouth || clampedEast <= clampedWest) return null;
  return {
    south: clampedSouth,
    north: clampedNorth,
    west: clampedWest,
    east: clampedEast,
  };
}

async function collectSelectionPoints(bounds) {
  const grid = data.selection_grid;
  if (!grid) throw new Error("Selection grid is not configured.");

  const values = await loadSelectionGrid();
  const selectedBounds = clampSelectionBounds(bounds);
  if (!selectedBounds) {
    return { points: [], min: NaN, max: NaN, mean: NaN };
  }

  const [[south, west], [north, east]] = grid.bounds;
  const rows = Number(grid.rows);
  const cols = Number(grid.cols);
  const latStep = (north - south) / rows;
  const lonStep = (east - west) / cols;
  const rowMin = clamp(Math.floor((selectedBounds.south - south) / latStep), 0, rows - 1);
  const rowMax = clamp(Math.floor((selectedBounds.north - south) / latStep), 0, rows - 1);
  const colMin = clamp(Math.floor((selectedBounds.west - west) / lonStep), 0, cols - 1);
  const colMax = clamp(Math.floor((selectedBounds.east - west) / lonStep), 0, cols - 1);
  const maxExportPoints = Number(grid.max_export_points) || 150000;

  const points = [];
  let min = Infinity;
  let max = -Infinity;
  let sum = 0;

  for (let row = rowMin; row <= rowMax; row += 1) {
    const lat = south + (row + 0.5) * latStep;
    const rowOffset = row * cols;
    for (let col = colMin; col <= colMax; col += 1) {
      const value = values[rowOffset + col];
      if (!Number.isFinite(value)) continue;
      if (value < state.rangeMin || value > state.rangeMax) continue;
      if (points.length >= maxExportPoints) {
        return { tooLarge: true, limit: maxExportPoints };
      }
      const lon = west + (col + 0.5) * lonStep;
      points.push([Number(lon.toFixed(6)), Number(lat.toFixed(6)), Number(value.toFixed(2))]);
      min = Math.min(min, value);
      max = Math.max(max, value);
      sum += value;
    }
  }

  return {
    points,
    min,
    max,
    mean: points.length ? sum / points.length : NaN,
  };
}

function selectionLabel(prefix) {
  const value = dom.selectionName.value.trim();
  if (value) return value;
  return `${prefix} ${state.selections.length + 1}`;
}

async function addSelectionFromBounds(bounds, prefix) {
  if (!bounds) {
    setSelectionStatus("Dessiner une zone ou utiliser la vue actuelle", "warning");
    return;
  }

  setSelectionLoading(true);
  setSelectionStatus("Calcul...");
  try {
    const result = await collectSelectionPoints(bounds);
    if (result.tooLarge) {
      setSelectionStatus(`Zone trop large > ${fmtNumber(result.limit)} pts`, "warning");
      return;
    }
    if (!result.points.length) {
      setSelectionStatus("Aucun point dans cette plage Tmrt", "warning");
      return;
    }

    const id = `S${Date.now()}_${state.selections.length + 1}`;
    state.selections.push({
      id,
      label: selectionLabel(prefix),
      rangeMin: state.rangeMin,
      rangeMax: state.rangeMax,
      points: result.points,
      min: result.min,
      max: result.max,
      mean: result.mean,
    });
    renderSelectionList();
    setSelectionStatus(`${fmtNumber(result.points.length)} points ajoutes`, "ready");
  } catch (error) {
    console.error(error);
    setSelectionStatus("Export impossible", "warning");
  } finally {
    setSelectionLoading(false);
  }
}

function csvCell(value) {
  const text = String(value ?? "");
  if (/[",\r\n]/.test(text)) return `"${text.replaceAll('"', '""')}"`;
  return text;
}

function exportSelectionsCsv() {
  if (!state.selections.length) {
    setSelectionStatus("Aucune zone exportable", "warning");
    return;
  }
  const lines = [
    [
      "selection_id",
      "selection_label",
      "longitude",
      "latitude",
      "tmrt_predite_c",
      "tmrt_filtre_min_c",
      "tmrt_filtre_max_c",
    ].join(","),
  ];

  for (const selection of state.selections) {
    for (const [lon, lat, value] of selection.points) {
      lines.push(
        [
          selection.id,
          selection.label,
          lon,
          lat,
          value,
          selection.rangeMin.toFixed(2),
          selection.rangeMax.toFixed(2),
        ]
          .map(csvCell)
          .join(","),
      );
    }
  }

  const blob = new Blob([`${lines.join("\r\n")}\r\n`], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `picopatt_tmrt_selections_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  setSelectionStatus("CSV exporte", "ready");
}

function clearSelectionShape() {
  if (state.selectionRectangle) {
    state.map.removeLayer(state.selectionRectangle);
    state.selectionRectangle = null;
  }
  state.selectionStart = null;
  state.selectionBounds = null;
  setSelectionStatus("Zone absente");
}

function setSelectionDrawing(isActive) {
  state.isSelectionDrawing = isActive;
  dom.selectionDrawButton.classList.toggle("active", isActive);
  dom.leafletMap.classList.toggle("selection-active", isActive);
  if (!state.map) return;
  if (isActive) {
    state.map.dragging.disable();
    state.map.doubleClickZoom.disable();
    setSelectionStatus("Tracer un rectangle sur la carte", "ready");
  } else {
    state.map.dragging.enable();
    state.map.doubleClickZoom.enable();
    if (!state.selectionBounds) setSelectionStatus("Zone absente");
  }
}

function handleSelectionMouseMove(event) {
  if (!state.selectionStart || !state.selectionRectangle) return;
  state.selectionRectangle.setBounds(L.latLngBounds(state.selectionStart, event.latlng));
}

function handleSelectionMouseUp() {
  state.map.off("mousemove", handleSelectionMouseMove);
  if (!state.selectionStart || !state.selectionRectangle) {
    setSelectionDrawing(false);
    return;
  }

  const bounds = state.selectionRectangle.getBounds();
  state.selectionStart = null;
  if (
    Math.abs(bounds.getEast() - bounds.getWest()) < 0.00005 ||
    Math.abs(bounds.getNorth() - bounds.getSouth()) < 0.00005
  ) {
    clearSelectionShape();
  } else {
    state.selectionBounds = bounds;
    setSelectionStatus("Zone prete a ajouter", "ready");
  }
  setSelectionDrawing(false);
}

function handleSelectionMouseDown(event) {
  if (!state.isSelectionDrawing) return;
  if (event.originalEvent?.button && event.originalEvent.button !== 0) return;
  L.DomEvent.preventDefault(event.originalEvent);

  if (state.selectionRectangle) {
    state.map.removeLayer(state.selectionRectangle);
  }
  state.selectionStart = event.latlng;
  state.selectionRectangle = L.rectangle(L.latLngBounds(event.latlng, event.latlng), {
    className: "selection-rectangle",
    color: "#00a77a",
    dashArray: "6 4",
    fillColor: "#00a77a",
    fillOpacity: 0.12,
    interactive: false,
    pane: "selectionPane",
    renderer: state.selectionRenderer,
    weight: 2.2,
  }).addTo(state.map);

  state.map.on("mousemove", handleSelectionMouseMove);
  state.map.once("mouseup", handleSelectionMouseUp);
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
  dom.selectionRangeLabel.textContent = `${fmtTemp(state.rangeMin)} - ${fmtTemp(state.rangeMax)}`;

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

  state.map.createPane("selectionPane");
  state.map.getPane("selectionPane").style.zIndex = 640;
  state.selectionRenderer = L.svg({ pane: "selectionPane", padding: 0.35 });
  updateSelectionPaneVisibility();

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
  state.map.on("mousedown", handleSelectionMouseDown);
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

  dom.panelTabs.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => setActivePanelTab(button.dataset.panelTab));
  });

  dom.selectionDrawButton.addEventListener("click", () => {
    setSelectionDrawing(!state.isSelectionDrawing);
  });

  dom.selectionAddButton.addEventListener("click", () => {
    addSelectionFromBounds(state.selectionBounds, "Zone");
  });

  dom.selectionViewportButton.addEventListener("click", () => {
    if (!state.map) return;
    addSelectionFromBounds(state.map.getBounds(), "Vue");
  });

  dom.selectionClearButton.addEventListener("click", () => {
    clearSelectionShape();
    setSelectionDrawing(false);
  });

  dom.selectionExportButton.addEventListener("click", exportSelectionsCsv);

  dom.selectionList.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-selection-id]");
    if (!button) return;
    state.selections = state.selections.filter((selection) => selection.id !== button.dataset.selectionId);
    renderSelectionList();
    setSelectionStatus(state.selections.length ? `${fmtNumber(state.selections.length)} zones exportables` : "Aucune zone exportable");
  });

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
renderSelectionList();
bindControls();
initLeafletMap();
