/**
 * SVV Trafikk-kort for Home Assistant
 * -----------------------------------
 * Et tilpassbart Lovelace-kort som viser trafikkdata fra Statens vegvesen.
 *
 * Design: minimalistisk og moderne. Rene SVG-ikoner (ingen emojier), lett
 * typografi, god luft, subtile flater. Diskré puls på statusprikken kun ved
 * aktive varsler (respekterer «redusert bevegelse»).
 *
 * Funksjoner:
 *  - Vertikal eller horisontal layout (config: layout)
 *  - Valgfritt kart (Leaflet + OpenStreetMap) som plotter aktive varsler
 *  - Konfigurerbare seksjoner, antall, og demo-/temavennlig
 *
 * Konfigurasjon (YAML):
 *   type: custom:svv-traffic-card
 *   entity: sensor.svv_trafikk_status
 *   title: Kristiansand                # valgfritt
 *   layout: vertical | horizontal      # standard: vertical
 *   show_map: true | false             # standard: false
 *   map_height: 220                     # px, valgfritt
 *   sections: [status, closures, incidents, travel_time,
 *              traffic_volume, weather, webcams]
 *   max_items: 5
 *   show_empty: false
 */

/* ---- Ikonsett: rene SVG-strektegninger (24x24, currentColor) ---- */
const ICONS = {
  check: '<path d="M20 6 9 17l-5-5"/>',
  alert: '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4m0 4h.01"/>',
  warning: '<circle cx="12" cy="12" r="9"/><path d="M12 8v4m0 4h.01"/>',
  question: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 0 1 4.5 1.5c0 1.5-2 2-2 3"/><path d="M12 17h.01"/>',
  roadworks: '<path d="M3 21h18"/><path d="m7 21 1.5-7h7L17 21"/><path d="M9 10h6l.6 4H8.4z"/><path d="M12 3v3"/>',
  accident: '<circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/><path d="M5 17H3v-4l2-4h8l4 4h2v4h-2M9 17h6"/>',
  closure: '<circle cx="12" cy="12" r="9"/><path d="m7 7 10 10"/>',
  congestion: '<rect x="2" y="11" width="8" height="6" rx="1.2"/><rect x="14" y="11" width="8" height="6" rx="1.2"/><path d="M4 11V8h4v3M16 11V8h4v3"/>',
  condition: '<path d="M7 16a4 4 0 0 1 0-8 5 5 0 0 1 9.6-1.3A3.5 3.5 0 0 1 17 16Z"/><path d="M8 20l1-2m3 2 1-2m3 2 1-2"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5m0-8h.01"/>',
  closures: '<rect x="3" y="9.5" width="18" height="2.6" rx="1"/><path d="M6 12v7m12-7v7M6 9.5V6m12 3.5V6"/>',
  incidents: '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4m0 4h.01"/>',
  travel_time: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  traffic_volume: '<path d="M3 3v18h18"/><rect x="7" y="12" width="2.6" height="6" rx=".5"/><rect x="11.7" y="8" width="2.6" height="10" rx=".5"/><rect x="16.4" y="5" width="2.6" height="13" rx=".5"/>',
  webcams: '<path d="m17 8 4-2v12l-4-2"/><rect x="3" y="6" width="14" height="12" rx="2"/>',
  weather: '<circle cx="12" cy="9" r="3.2"/><path d="M12 2.5v1.2m0 10.6v1.2M4.8 9H3.6m16.8 0h-1.2M7 4l.8.8m8.4 8.4.8.8M7 14l.8-.8m8.4-8.4.8-.8"/><path d="M8 20h8"/>',
  chevronLeft: '<path d="m15 18-6-6 6-6"/>',
  chevronRight: '<path d="m9 18 6-6-6-6"/>',
  trendUp: '<path d="M3 17 9 11l4 4 8-8M21 7v5m0-5h-5"/>',
  trendDown: '<path d="M3 7 9 13l4-4 8 8M21 17v-5m0 5h-5"/>',
  trendStable: '<path d="M4 12h16m-5-5 5 5-5 5"/>',
  cameraOff: '<path d="M3 3l18 18M21 7l-4 2v6M3 7v10h12"/>',
  map: '<path d="m9 4-6 2v14l6-2 6 2 6-2V4l-6 2-6-2Z"/><path d="M9 4v14m6-10v14"/>',
};

function svg(name, opts = {}) {
  const body = ICONS[name] || ICONS.info;
  const size = opts.size || 20;
  const sw = opts.stroke || 1.8;
  return `<svg class="ic" width="${size}" height="${size}" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" stroke-width="${sw}"
    stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${body}</svg>`;
}

const STATUS_META = {
  ok:      { label: "Normal trafikk", color: "#16a34a", soft: "rgba(22,163,74,.12)",  icon: "check" },
  warning: { label: "Forsinkelser",   color: "#d97706", soft: "rgba(217,119,6,.12)",  icon: "warning" },
  alert:   { label: "Aktive varsler", color: "#dc2626", soft: "rgba(220,38,38,.12)",  icon: "alert" },
  unknown: { label: "Ukjent",         color: "#64748b", soft: "rgba(100,116,139,.12)",icon: "question" },
};

const SECTION_LABELS = {
  incidents: "Veimeldinger",
  closures: "Stengte veier og tunneler",
  traffic_volume: "Trafikkmengde",
  travel_time: "Reisetid",
  webcams: "Webkamera",
  weather: "Kjøreforhold",
};

const CATEGORY_ICON = {
  roadworks: "roadworks", accident: "accident", closure: "closure",
  congestion: "congestion", condition: "condition", other: "info",
};

const ALL_SECTIONS = [
  "status", "closures", "incidents", "travel_time",
  "traffic_volume", "weather", "webcams",
];

/* ----------------------------------------------------------------------------
 * Intern, avhengighetsfri kartrenderer ("slippy map").
 *
 * Vi bruker IKKE Leaflet, fordi Leaflet har kjente problemer med å rendre inni
 * shadow DOM (som dette kortet bruker). I stedet henter vi OpenStreetMap-fliser
 * direkte og plasserer dem i en enkel beholder, med fargekodede markører oppå.
 * Dette gir full kontroll på utseendet, ingen ekstern bibliotek-lasting, og
 * fungerer pålitelig i shadow DOM.
 *
 * Web-Mercator-projeksjon (samme som OSM/Google):
 * ------------------------------------------------------------------------- */
const TILE_SIZE = 256;
const SVV_TILE_URL = "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png";
const SVV_TILE_SUBDOMAINS = ["a", "b", "c", "d"];

function lonToX(lon, z) {
  return ((lon + 180) / 360) * Math.pow(2, z);
}
function latToY(lat, z) {
  const r = (lat * Math.PI) / 180;
  return (
    (1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2
  ) * Math.pow(2, z);
}

/* Velg et zoomnivå som rommer alle punktene innenfor gitt pikselstørrelse. */
function fitZoom(points, widthPx, heightPx) {
  if (points.length === 1) return 12;
  let minLat = 90, maxLat = -90, minLon = 180, maxLon = -180;
  for (const p of points) {
    minLat = Math.min(minLat, p.latitude); maxLat = Math.max(maxLat, p.latitude);
    minLon = Math.min(minLon, p.longitude); maxLon = Math.max(maxLon, p.longitude);
  }
  for (let z = 13; z >= 4; z--) {
    const xs = [lonToX(minLon, z), lonToX(maxLon, z)];
    const ys = [latToY(maxLat, z), latToY(minLat, z)];
    const w = Math.abs(xs[1] - xs[0]) * TILE_SIZE;
    const h = Math.abs(ys[1] - ys[0]) * TILE_SIZE;
    if (w <= widthPx * 0.82 && h <= heightPx * 0.82) return z;
  }
  return 5;
}

class SvvTrafficCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._webcamIndex = {};
    this._map = null;
    this._mapMarkers = [];
    this._mapKey = "";
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Du må angi 'entity' (SVV-statussensoren).");
    }
    this._config = {
      sections: ALL_SECTIONS,
      max_items: 5,
      show_empty: false,
      layout: "vertical",
      show_map: false,
      map_height: 220,
      ...config,
    };
    // Kartet bygges utenom innerHTML, så vi nullstiller referansen ved ny config
    this._destroyMap();
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    const base = this._config.layout === "horizontal" ? 4 : 6;
    return base + (this._config.show_map ? 3 : 0);
  }

  _getData() {
    if (!this._hass) return null;
    const ent = this._hass.states[this._config.entity];
    if (!ent) return null;
    return ent.attributes.data || null;
  }

  _statusMeta(status) { return STATUS_META[status] || STATUS_META.unknown; }

  _render() {
    if (!this._hass || !this._config.entity) return;
    const ent = this._hass.states[this._config.entity];
    const data = this._getData();

    if (!ent) {
      this.shadowRoot.innerHTML = this._styles() +
        `<ha-card><div class="missing">Fant ikke entiteten
         <code>${this._config.entity}</code></div></ha-card>`;
      return;
    }

    const overall = (data && data.overall_status) || ent.state || "unknown";
    const meta = this._statusMeta(overall);
    const title = this._config.title ||
      (data && data.area_name ? data.area_name : "SVV Trafikk");
    const sections = this._config.sections;
    const horizontal = this._config.layout === "horizontal";

    const parts = [];
    parts.push(this._renderHeader(title, meta, overall, data));

    // Kart-container (fylles av Leaflet etter render)
    if (this._config.show_map) {
      parts.push(`<div class="map-wrap" style="height:${this._config.map_height}px">
          <div class="map" id="svvmap"></div>
        </div>`);
    }

    const body = [];
    if (data) {
      if (sections.includes("closures"))       body.push(this._renderIncidentList(data.closures, "closures"));
      if (sections.includes("incidents"))      body.push(this._renderIncidentList(data.incidents, "incidents"));
      if (sections.includes("travel_time"))    body.push(this._renderTravelTimes(data.travel_times));
      if (sections.includes("traffic_volume")) body.push(this._renderVolume(data.traffic_volume));
      if (sections.includes("weather"))        body.push(this._renderWeather(data.weather));
      if (sections.includes("webcams"))        body.push(this._renderWebcams(data.webcams));
    } else {
      body.push(`<div class="empty">Ingen data tilgjengelig ennå.</div>`);
    }
    const bodyHtml = body.filter(Boolean).join("");
    parts.push(`<div class="body ${horizontal ? "grid" : ""}">${bodyHtml}</div>`);

    if (data && data.errors && data.errors.length) {
      parts.push(`<div class="errors">${data.errors.map(e =>
        `<div class="error-row">${svg("info",{size:15})}<span>${this._esc(e)}</span></div>`).join("")}</div>`);
    }

    const updated = data && data.last_updated
      ? new Date(data.last_updated).toLocaleTimeString("no-NO",
          { hour: "2-digit", minute: "2-digit" })
      : "—";
    parts.push(`<div class="footer">
        <span>Statens vegvesen · NLOD</span>
        <span>Oppdatert ${updated}</span>
      </div>`);

    this.shadowRoot.innerHTML = this._styles() +
      `<ha-card class="status-${overall} layout-${this._config.layout}">${parts.join("")}</ha-card>`;

    this._attachHandlers();
    if (this._config.show_map) this._setupMap(data);
  }

  _renderHeader(title, meta, overall, data) {
    const pulse = overall === "alert" ? "pulse" : "";
    const counts = data ? [
      { n: (data.closures || []).length, l: "stengt" },
      { n: (data.incidents || []).length, l: "meldinger" },
      { n: (data.webcams || []).length, l: "kamera" },
    ] : [];
    const summary = counts.length ? `<div class="summary">${counts.map(c => `
      <div class="sum"><span class="sum-n">${c.n}</span><span class="sum-l">${c.l}</span></div>`
      ).join('<span class="sum-div"></span>')}</div>` : "";
    return `
      <div class="header">
        <div class="status-dot ${pulse}" style="color:${meta.color};background:${meta.soft}">
          ${svg(meta.icon, { size: 21, stroke: 2 })}
        </div>
        <div class="header-text">
          <div class="title">${this._esc(title)}</div>
          <div class="status-line" style="color:${meta.color}">${meta.label}</div>
        </div>
      </div>
      ${summary}`;
  }

  _section(kind, inner, count) {
    const label = SECTION_LABELS[kind];
    const badge = count != null && count > 0
      ? `<span class="count-badge">${count}</span>` : "";
    return `<section class="section">
        <div class="section-head">
          <span class="section-ic">${svg(kind, { size: 16, stroke: 1.8 })}</span>
          <span class="section-label">${this._esc(label)}</span>
          ${badge}
        </div>
        <div class="section-body">${inner}</div>
      </section>`;
  }

  _renderIncidentList(list, kind) {
    list = list || [];
    if (!list.length && !this._config.show_empty) return "";
    if (!list.length) {
      return this._section(kind,
        `<div class="empty-row">Ingen ${SECTION_LABELS[kind].toLowerCase()}</div>`, 0);
    }
    const rows = list.slice(0, this._config.max_items).map(inc => {
      const m = this._statusMeta(inc.severity);
      const iconName = CATEGORY_ICON[inc.category] || CATEGORY_ICON.other;
      const when = inc.start_time
        ? new Date(inc.start_time).toLocaleString("no-NO",
            { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })
        : "";
      return `
        <div class="row">
          <div class="row-ic" style="color:${m.color};background:${m.soft}">
            ${svg(iconName, { size: 17, stroke: 1.8 })}
          </div>
          <div class="row-body">
            <div class="row-title">${this._esc(inc.title || "Veimelding")}</div>
            ${inc.description ? `<div class="row-desc">${this._esc(inc.description)}</div>` : ""}
            <div class="row-meta">
              ${inc.road ? `<span class="chip chip-road">${this._esc(inc.road)}</span>` : ""}
              ${inc.county ? `<span class="chip">${this._esc(inc.county)}</span>` : ""}
              ${when ? `<span class="chip chip-time">${when}</span>` : ""}
            </div>
          </div>
        </div>`;
    }).join("");
    const more = list.length > this._config.max_items
      ? `<div class="more">+${list.length - this._config.max_items} flere</div>` : "";
    return this._section(kind, rows + more, list.length);
  }

  _renderTravelTimes(list) {
    list = list || [];
    if (!list.length && !this._config.show_empty) return "";
    if (!list.length) return this._section("travel_time", `<div class="empty-row">Ingen reisetidsdata</div>`, 0);
    const trendIcon = { increasing: "trendUp", decreasing: "trendDown", stable: "trendStable" };
    const rows = list.slice(0, this._config.max_items).map(t => {
      const m = this._statusMeta(t.status);
      const mins = t.travel_time_seconds != null ? Math.round(t.travel_time_seconds / 60) : "—";
      const delay = t.delay_seconds != null && t.delay_seconds > 0
        ? `+${Math.round(t.delay_seconds / 60)} min` : "";
      const trend = trendIcon[t.trend];
      return `
        <div class="data-row">
          <div class="data-name">${this._esc(t.name)}</div>
          <div class="data-val">
            ${delay ? `<span class="delay" style="color:${m.color}">${delay}</span>` : ""}
            <span class="big" style="color:${m.color}">${mins}<span class="unit">min</span></span>
            ${trend ? `<span class="trend" style="color:${m.color}">${svg(trend,{size:15,stroke:2})}</span>` : ""}
          </div>
        </div>`;
    }).join("");
    return this._section("travel_time", rows, list.length);
  }

  _renderVolume(list) {
    list = list || [];
    if (!list.length && !this._config.show_empty) return "";
    if (!list.length) return this._section("traffic_volume", `<div class="empty-row">Ingen passeringsdata</div>`, 0);
    const max = Math.max(...list.map(p => p.volume || 0), 1);
    const rows = list.slice(0, this._config.max_items).map(p => {
      const pct = Math.round(((p.volume || 0) / max) * 100);
      return `
        <div class="vol-row">
          <div class="vol-name">${this._esc(p.name)}</div>
          <div class="vol-track"><div class="vol-fill" style="width:${pct}%"></div></div>
          <div class="vol-num">${p.volume != null ? p.volume : "—"}</div>
        </div>`;
    }).join("");
    return this._section("traffic_volume",
      `<div class="vol-wrap">${rows}</div><div class="vol-unit">kjøretøy per time</div>`, list.length);
  }

  _renderWeather(list) {
    list = list || [];
    if (!list.length && !this._config.show_empty) return "";
    if (!list.length) return this._section("weather", `<div class="empty-row">Ingen værdata</div>`, 0);
    const rows = list.slice(0, this._config.max_items).map(w => {
      const m = this._statusMeta(w.status);
      const vals = [];
      if (w.air_temperature != null) vals.push(`<span class="w-main">${w.air_temperature}°</span>`);
      if (w.road_temperature != null) vals.push(`<span class="w-sub">veg ${w.road_temperature}°</span>`);
      if (w.wind_speed != null) vals.push(`<span class="w-sub">${w.wind_speed} m/s</span>`);
      return `
        <div class="data-row">
          <div class="data-name"><span class="w-dot" style="background:${m.color}"></span>${this._esc(w.name)}</div>
          <div class="data-val">${vals.join("")}</div>
        </div>`;
    }).join("");
    return this._section("weather", rows, list.length);
  }

  _renderWebcams(list) {
    list = list || [];
    if (!list.length && !this._config.show_empty) return "";
    if (!list.length) return this._section("webcams", `<div class="empty-row">Ingen kamera i området</div>`, 0);
    const key = this._config.entity;
    const idx = Math.min(this._webcamIndex[key] || 0, list.length - 1);
    const cam = list[idx];
    const dots = list.length > 1 ? list.map((_, i) =>
      `<span class="dot ${i === idx ? "dot-on" : ""}" data-cam="${i}"></span>`).join("") : "";
    const img = cam.image_url
      ? `<img class="cam-img" src="${cam.image_url}" alt="${this._esc(cam.name)}" referrerpolicy="no-referrer" loading="lazy">`
      : `<div class="cam-missing">${svg("cameraOff",{size:26,stroke:1.5})}<span>Bilde utilgjengelig</span></div>`;
    const nav = list.length > 1;
    return this._section("webcams", `
      <div class="cam">
        ${nav ? `<button class="cam-nav cam-prev" data-nav="-1" aria-label="Forrige">${svg("chevronLeft",{size:19})}</button>` : ""}
        ${img}
        ${nav ? `<button class="cam-nav cam-next" data-nav="1" aria-label="Neste">${svg("chevronRight",{size:19})}</button>` : ""}
        <div class="cam-name">${this._esc(cam.name)}</div>
      </div>
      ${nav ? `<div class="cam-dots">${dots}</div>` : ""}`, list.length);
  }

  /* ---- Kart ---- */
  _mapPoints(data) {
    if (!data) return [];
    const pts = [];
    (data.closures || []).forEach(c => {
      if (c.latitude != null && c.longitude != null)
        pts.push({ ...c, _kind: "closure" });
    });
    (data.incidents || []).forEach(i => {
      if (i.latitude != null && i.longitude != null)
        pts.push({ ...i, _kind: "incident" });
    });
    return pts;
  }

  async _setupMap(data) {
    const points = this._mapPoints(data);
    const el = this.shadowRoot.getElementById("svvmap");
    if (!el) return;

    // Mål beholderen (kan være 0 rett etter innerHTML – prøv da igjen)
    const w = el.clientWidth;
    const h = el.clientHeight;
    if (!w || !h) {
      requestAnimationFrame(() => this._setupMap(data));
      return;
    }

    // Senterpunkt: gjennomsnitt av punktene, ellers midt i Norge
    let centerLat = 60.5, centerLon = 8.5, zoom = 5;
    if (points.length) {
      centerLat = points.reduce((s, p) => s + p.latitude, 0) / points.length;
      centerLon = points.reduce((s, p) => s + p.longitude, 0) / points.length;
      zoom = fitZoom(points, w, h);
    }

    // Verdens-pikselkoordinat for senter på valgt zoom
    const cx = lonToX(centerLon, zoom) * TILE_SIZE;
    const cy = latToY(centerLat, zoom) * TILE_SIZE;
    // Øvre venstre hjørne av visningen i verdens-piksler
    const originX = cx - w / 2;
    const originY = cy - h / 2;

    // Hvilke fliser dekker visningen?
    const x0 = Math.floor(originX / TILE_SIZE);
    const y0 = Math.floor(originY / TILE_SIZE);
    const x1 = Math.floor((originX + w) / TILE_SIZE);
    const y1 = Math.floor((originY + h) / TILE_SIZE);
    const maxIdx = Math.pow(2, zoom);

    const tiles = [];
    let sIdx = 0;
    for (let tx = x0; tx <= x1; tx++) {
      for (let ty = y0; ty <= y1; ty++) {
        if (ty < 0 || ty >= maxIdx) continue;
        const wrappedX = ((tx % maxIdx) + maxIdx) % maxIdx;
        const sub = SVV_TILE_SUBDOMAINS[sIdx++ % SVV_TILE_SUBDOMAINS.length];
        const url = SVV_TILE_URL
          .replace("{s}", sub).replace("{z}", zoom)
          .replace("{x}", wrappedX).replace("{y}", ty);
        const left = tx * TILE_SIZE - originX;
        const top = ty * TILE_SIZE - originY;
        tiles.push(
          `<img class="svv-tile" src="${url}" loading="lazy" alt=""
             referrerpolicy="no-referrer"
             style="left:${left}px;top:${top}px" draggable="false">`
        );
      }
    }

    // Markører – plasseres på samme projeksjon
    const markers = points.map((p, i) => {
      const meta = this._statusMeta(p.severity);
      const px = lonToX(p.longitude, zoom) * TILE_SIZE - originX;
      const py = latToY(p.latitude, zoom) * TILE_SIZE - originY;
      const road = p.road ? `${this._esc(p.road)} · ` : "";
      const title = `${road}${this._esc(p.title || "Veimelding")}`;
      return `
        <div class="svv-marker" style="left:${px}px;top:${py}px"
             data-mk="${i}" tabindex="0" role="button"
             title="${title}">
          <span class="svv-pin" style="background:${meta.color}"></span>
        </div>`;
    }).join("");

    const popups = points.map((p, i) => {
      const meta = this._statusMeta(p.severity);
      const px = lonToX(p.longitude, zoom) * TILE_SIZE - originX;
      const py = latToY(p.latitude, zoom) * TILE_SIZE - originY;
      const road = p.road ? `<b>${this._esc(p.road)}</b> · ` : "";
      return `
        <div class="svv-popup" id="popup-${i}" style="left:${px}px;top:${py}px;border-color:${meta.color}">
          <div class="svv-popup-title">${road}${this._esc(p.title || "Veimelding")}</div>
          ${p.location_description ? `<div class="svv-popup-sub">${this._esc(p.location_description)}</div>` : ""}
        </div>`;
    }).join("");

    el.innerHTML = `
      <div class="svv-tiles">${tiles.join("")}</div>
      <div class="svv-markers">${markers}${popups}</div>
      <div class="svv-attr">© OpenStreetMap, © CARTO</div>`;

    // Klikk på markør → vis/skjul tilhørende popup
    el.querySelectorAll("[data-mk]").forEach(mk => {
      const toggle = () => {
        const i = mk.getAttribute("data-mk");
        const wasOpen = el.querySelector(`#popup-${i}`).classList.contains("open");
        el.querySelectorAll(".svv-popup").forEach(pp => pp.classList.remove("open"));
        if (!wasOpen) el.querySelector(`#popup-${i}`).classList.add("open");
      };
      mk.addEventListener("click", toggle);
      mk.addEventListener("keydown", e => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); }
      });
    });
  }

  _destroyMap() {
    // Den interne kartrendereren trenger ingen opprydding utover DOM-en,
    // som fjernes automatisk når kortet rendres på nytt.
    this._map = null;
  }

  disconnectedCallback() { this._destroyMap(); }

  _attachHandlers() {
    const root = this.shadowRoot;
    const key = this._config.entity;
    const data = this._getData();
    const cams = (data && data.webcams) || [];
    root.querySelectorAll("[data-nav]").forEach(btn => {
      btn.addEventListener("click", () => {
        const dir = parseInt(btn.getAttribute("data-nav"), 10);
        const cur = this._webcamIndex[key] || 0;
        this._webcamIndex[key] = (cur + dir + cams.length) % cams.length;
        this._render();
      });
    });
    root.querySelectorAll("[data-cam]").forEach(dot => {
      dot.addEventListener("click", () => {
        this._webcamIndex[key] = parseInt(dot.getAttribute("data-cam"), 10);
        this._render();
      });
    });
  }

  _esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  _styles() {
    return `<style>
      :host { --svv-radius: 18px; }
      * { box-sizing: border-box; }
      ha-card {
        overflow: hidden; padding: 0;
        font-family: var(--paper-font-body1_-_font-family, system-ui, -apple-system, sans-serif);
        -webkit-font-smoothing: antialiased;
      }
      .ic { display: block; flex: 0 0 auto; }

      /* Header */
      .header { display: flex; align-items: center; gap: 13px; padding: 20px 22px 0; }
      .status-dot {
        width: 42px; height: 42px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center; flex: 0 0 auto;
      }
      .status-dot.pulse { animation: svvpulse 2.2s ease-in-out infinite; }
      @keyframes svvpulse {
        0%,100% { box-shadow: 0 0 0 0 rgba(220,38,38,.3); }
        50%     { box-shadow: 0 0 0 7px rgba(220,38,38,0); }
      }
      @media (prefers-reduced-motion: reduce) { .status-dot.pulse { animation: none; } }
      .header-text { min-width: 0; flex: 1; }
      .title {
        font-size: 1.22rem; font-weight: 600; line-height: 1.2; letter-spacing: -.015em;
        color: var(--primary-text-color);
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
      }
      .status-line { font-size: .84rem; font-weight: 500; margin-top: 2px; }

      /* Sammendrag */
      .summary {
        display: flex; align-items: center; gap: 4px;
        margin: 16px 22px 4px; padding: 0;
      }
      .sum { display: flex; flex-direction: column; align-items: center; gap: 1px; flex: 1; }
      .sum-n { font-size: 1.5rem; font-weight: 650; line-height: 1;
        color: var(--primary-text-color); font-variant-numeric: tabular-nums;
        letter-spacing: -.02em; }
      .sum-l { font-size: .68rem; text-transform: uppercase; letter-spacing: .5px;
        color: var(--secondary-text-color); font-weight: 500; }
      .sum-div { width: 1px; height: 26px; background: var(--divider-color); }

      /* Kart */
      .map-wrap { margin: 16px 22px 0; border-radius: 14px; overflow: hidden;
        border: 1px solid var(--divider-color); }
      .map { width: 100%; height: 100%; position: relative; overflow: hidden;
        background: var(--secondary-background-color); cursor: default; }
      .svv-tiles, .svv-markers { position: absolute; inset: 0; }
      .svv-tile { position: absolute; width: 256px; height: 256px;
        user-select: none; -webkit-user-drag: none; }
      .svv-markers { pointer-events: none; }
      .svv-marker { position: absolute; transform: translate(-50%, -100%);
        pointer-events: auto; cursor: pointer; padding: 4px; }
      .svv-pin { display: block; width: 16px; height: 16px; border-radius: 50% 50% 50% 0;
        transform: rotate(45deg); border: 2px solid #fff;
        box-shadow: 0 1px 4px rgba(0,0,0,.4); transition: transform .15s; }
      .svv-marker:hover .svv-pin, .svv-marker:focus .svv-pin {
        transform: rotate(45deg) scale(1.18); }
      .svv-marker:focus { outline: none; }
      .svv-popup { position: absolute; transform: translate(-50%, calc(-100% - 14px));
        background: var(--card-background-color); color: var(--primary-text-color);
        border: 1px solid; border-left-width: 3px; border-radius: 9px;
        padding: 8px 11px; min-width: 150px; max-width: 230px; z-index: 5;
        box-shadow: 0 6px 20px rgba(0,0,0,.18);
        opacity: 0; visibility: hidden; transition: opacity .15s; pointer-events: none; }
      .svv-popup.open { opacity: 1; visibility: visible; }
      .svv-popup-title { font-size: .8rem; font-weight: 600; line-height: 1.3; }
      .svv-popup-sub { font-size: .72rem; color: var(--secondary-text-color); margin-top: 2px; }
      .svv-attr { position: absolute; right: 0; bottom: 0; z-index: 4;
        font-size: .6rem; color: var(--secondary-text-color);
        background: color-mix(in srgb, var(--card-background-color) 78%, transparent);
        padding: 1px 6px; border-radius: 6px 0 0 0; }

      /* Body */
      .body { padding: 4px 22px 0; }
      .body.grid {
        display: grid; gap: 0 26px;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        align-items: start;
      }
      .section { padding: 16px 0; border-top: 1px solid var(--divider-color); }
      .body:not(.grid) .section:first-child { border-top: 0; }
      .body.grid .section { border-top: 0; border-bottom: 1px solid var(--divider-color); }
      .section-head { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
      .section-ic { color: var(--secondary-text-color); display: flex; opacity: .85; }
      .section-label {
        font-size: .7rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: .8px; color: var(--secondary-text-color); flex: 1;
      }
      .count-badge {
        font-size: .7rem; font-weight: 600; min-width: 19px; height: 19px; padding: 0 6px;
        border-radius: 10px; background: var(--secondary-background-color);
        color: var(--secondary-text-color);
        display: inline-flex; align-items: center; justify-content: center;
        font-variant-numeric: tabular-nums;
      }

      /* Hendelsesrad */
      .row { display: flex; gap: 12px; padding: 11px 13px; margin-bottom: 7px;
        background: var(--secondary-background-color); border-radius: 13px; }
      .row:last-child { margin-bottom: 0; }
      .row-ic { width: 34px; height: 34px; border-radius: 10px; flex: 0 0 auto;
        display: flex; align-items: center; justify-content: center; }
      .row-body { min-width: 0; flex: 1; }
      .row-title { font-weight: 600; font-size: .91rem; line-height: 1.3;
        color: var(--primary-text-color); }
      .row-desc { font-size: .81rem; color: var(--secondary-text-color);
        margin-top: 3px; line-height: 1.45; }
      .row-meta { margin-top: 9px; display: flex; flex-wrap: wrap; gap: 6px; }
      .chip { font-size: .69rem; font-weight: 600; padding: 3px 8px; border-radius: 7px;
        background: transparent; color: var(--secondary-text-color);
        border: 1px solid var(--divider-color); }
      .chip-road { background: var(--primary-color); color: #fff; border-color: transparent; }
      .chip-time { font-variant-numeric: tabular-nums; }
      .more { font-size: .77rem; color: var(--secondary-text-color); text-align: center; padding: 6px; }
      .empty-row { font-size: .84rem; color: var(--secondary-text-color); padding: 2px 2px 6px; }

      /* Data-rad */
      .data-row { display: flex; align-items: center; gap: 12px; padding: 10px 0;
        border-bottom: 1px solid var(--divider-color); }
      .data-row:last-child { border-bottom: 0; }
      .data-name { flex: 1; font-size: .89rem; color: var(--primary-text-color); min-width: 0;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        display: flex; align-items: center; gap: 8px; }
      .data-val { display: flex; align-items: center; gap: 9px; flex: 0 0 auto; }
      .big { font-size: 1.1rem; font-weight: 650; line-height: 1;
        font-variant-numeric: tabular-nums; letter-spacing: -.01em; }
      .big .unit { font-size: .7rem; font-weight: 500; margin-left: 3px; opacity: .7; }
      .delay { font-size: .75rem; font-weight: 600; font-variant-numeric: tabular-nums; }
      .trend { display: flex; }

      /* Trafikkmengde */
      .vol-wrap { display: flex; flex-direction: column; gap: 11px; }
      .vol-row { display: flex; align-items: center; gap: 12px; }
      .vol-name { flex: 0 0 32%; font-size: .85rem; color: var(--primary-text-color);
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .vol-track { flex: 1; height: 6px; border-radius: 99px;
        background: var(--divider-color); overflow: hidden; }
      .vol-fill { height: 100%; border-radius: 99px; background: var(--primary-color);
        transition: width .7s cubic-bezier(.4,0,.2,1); }
      .vol-num { flex: 0 0 auto; min-width: 42px; text-align: right; font-size: .86rem;
        font-weight: 650; color: var(--primary-text-color); font-variant-numeric: tabular-nums; }
      .vol-unit { font-size: .7rem; color: var(--secondary-text-color); text-align: right; margin-top: 10px; }

      .w-dot { width: 7px; height: 7px; border-radius: 50%; flex: 0 0 auto; }
      .w-main { font-size: 1.02rem; font-weight: 650; color: var(--primary-text-color);
        font-variant-numeric: tabular-nums; }
      .w-sub { font-size: .75rem; color: var(--secondary-text-color); }

      /* Webkamera */
      .cam { position: relative; border-radius: 13px; overflow: hidden; background: #0b0e12;
        aspect-ratio: 16/9; display: flex; align-items: center; justify-content: center; }
      .cam-img { width: 100%; height: 100%; object-fit: cover; display: block; }
      .cam-missing { color: #8b94a0; font-size: .8rem; display: flex; flex-direction: column;
        align-items: center; gap: 8px; }
      .cam-name { position: absolute; left: 0; right: 0; bottom: 0; padding: 20px 13px 10px;
        font-size: .79rem; color: #fff; font-weight: 600;
        background: linear-gradient(transparent, rgba(0,0,0,.7));
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .cam-nav { position: absolute; top: 50%; transform: translateY(-50%);
        width: 34px; height: 34px; border: 0; border-radius: 50%;
        background: rgba(15,18,22,.5); color: #fff; cursor: pointer; z-index: 2;
        display: flex; align-items: center; justify-content: center;
        backdrop-filter: blur(4px); transition: background .2s; }
      .cam-nav:hover { background: rgba(15,18,22,.78); }
      .cam-prev { left: 10px; } .cam-next { right: 10px; }
      .cam-dots { display: flex; gap: 6px; justify-content: center; padding: 12px 0 2px; }
      .dot { width: 6px; height: 6px; border-radius: 50%; cursor: pointer;
        background: var(--divider-color); transition: all .2s; }
      .dot-on { background: var(--primary-color); transform: scale(1.3); }

      /* Feil + footer */
      .errors { margin: 12px 22px 0; padding: 10px 12px; background: rgba(217,119,6,.1);
        color: #b45309; border-radius: 11px; font-size: .79rem; }
      .error-row { display: flex; align-items: center; gap: 8px; }
      .footer { display: flex; justify-content: space-between; align-items: center;
        padding: 14px 22px; margin-top: 12px; font-size: .69rem;
        color: var(--secondary-text-color); border-top: 1px solid var(--divider-color);
        font-variant-numeric: tabular-nums; }
      .missing, .empty { padding: 26px 22px; color: var(--secondary-text-color); font-size: .89rem; }
      code { background: var(--secondary-background-color); padding: 2px 6px; border-radius: 5px; font-size: .85em; }
    </style>`;
  }

  /* ---- Visuell editor (grafisk konfigurasjon i HA) ---- */
  static getConfigElement() {
    return document.createElement("svv-traffic-card-editor");
  }

  static getStubConfig(hass) {
    // Forsøk å finne en SVV-statussensor automatisk
    let entity = "sensor.svv_trafikk_status";
    if (hass && hass.states) {
      const match = Object.keys(hass.states).find(
        e => e.startsWith("sensor.") && e.includes("svv") && e.includes("status")
      );
      if (match) entity = match;
    }
    return {
      entity,
      layout: "vertical",
      show_map: false,
      sections: ALL_SECTIONS,
      max_items: 5,
    };
  }
}

/* ===========================================================================
 * Visuell editor: svv-traffic-card-editor
 * Lar brukeren sette opp kortet med nedtrekksmenyer og avkrysningsbokser i
 * stedet for å skrive YAML. Følger HAs editor-mønster (config-changed-event).
 * ======================================================================== */
class SvvTrafficCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._rendered = false;
  }

  setConfig(config) {
    this._config = { sections: ALL_SECTIONS, ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _emit() {
    this.dispatchEvent(new CustomEvent("config-changed", {
      detail: { config: this._config },
      bubbles: true, composed: true,
    }));
  }

  _update(key, value) {
    this._config = { ...this._config, [key]: value };
    this._emit();
  }

  _toggleSection(name, on) {
    const set = new Set(this._config.sections || ALL_SECTIONS);
    if (on) set.add(name); else set.delete(name);
    // Bevar standard rekkefølge
    this._config = {
      ...this._config,
      sections: ALL_SECTIONS.filter(s => set.has(s)),
    };
    this._emit();
  }

  _statusEntities() {
    if (!this._hass) return [];
    return Object.keys(this._hass.states)
      .filter(e => e.startsWith("sensor."))
      .filter(e => {
        const a = this._hass.states[e].attributes || {};
        // SVV-statussensoren har en "data"-blokk med area_name
        return a.data && typeof a.data === "object" && "overall_status" in a.data;
      });
  }

  _render() {
    const c = this._config;
    const sections = new Set(c.sections || ALL_SECTIONS);

    // Foreslå SVV-sensorer øverst, men tillat hvilken som helst sensor
    const svvEntities = this._statusEntities();
    const allSensors = this._hass
      ? Object.keys(this._hass.states).filter(e => e.startsWith("sensor.")).sort()
      : [];
    const entityList = svvEntities.length ? svvEntities : allSensors;
    const options = entityList.map(e => {
      const name = this._hass.states[e].attributes.friendly_name || e;
      const sel = e === c.entity ? "selected" : "";
      return `<option value="${e}" ${sel}>${this._esc(name)}</option>`;
    }).join("");

    const sectionRows = Object.keys(SECTION_LABELS).map(key => `
      <label class="row">
        <input type="checkbox" data-section="${key}" ${sections.has(key) ? "checked" : ""}>
        <span>${this._esc(SECTION_LABELS[key])}</span>
      </label>`).join("");

    this.shadowRoot.innerHTML = `
      <style>
        .editor { display: flex; flex-direction: column; gap: 18px;
          font-family: var(--paper-font-body1_-_font-family, system-ui, sans-serif);
          color: var(--primary-text-color); padding: 4px 0; }
        .field { display: flex; flex-direction: column; gap: 6px; }
        .label { font-size: .8rem; font-weight: 600; color: var(--primary-text-color); }
        .hint { font-size: .73rem; color: var(--secondary-text-color); }
        select, input[type="text"], input[type="number"] {
          padding: 9px 11px; border-radius: 9px; font-size: .9rem;
          border: 1px solid var(--divider-color);
          background: var(--card-background-color, #fff);
          color: var(--primary-text-color); width: 100%; box-sizing: border-box; }
        .seg { display: flex; gap: 6px; }
        .seg button {
          flex: 1; padding: 9px; border-radius: 9px; cursor: pointer; font-weight: 600;
          font-size: .85rem; border: 1px solid var(--divider-color);
          background: var(--card-background-color, #fff); color: var(--primary-text-color); }
        .seg button.on { background: var(--primary-color); color: #fff;
          border-color: var(--primary-color); }
        .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
        .checks { display: flex; flex-direction: column; gap: 4px;
          border: 1px solid var(--divider-color); border-radius: 10px; padding: 10px 12px; }
        .row { display: flex; align-items: center; gap: 10px; font-size: .88rem;
          cursor: pointer; padding: 3px 0; }
        .row input { width: 17px; height: 17px; accent-color: var(--primary-color); }
        .switch-row { display: flex; align-items: center; justify-content: space-between; }
      </style>
      <div class="editor">
        <div class="field">
          <span class="label">Statussensor</span>
          <select id="entity">${options || '<option>Ingen sensorer funnet</option>'}</select>
          <span class="hint">Velg SVV-statussensoren for området du vil vise.</span>
        </div>

        <div class="field">
          <span class="label">Tittel (valgfritt)</span>
          <input type="text" id="title" value="${this._esc(c.title || "")}"
            placeholder="F.eks. Trafikk – Kristiansand">
        </div>

        <div class="field">
          <span class="label">Layout</span>
          <div class="seg" id="layout">
            <button data-v="vertical" class="${(c.layout||'vertical')==='vertical'?'on':''}">Vertikal</button>
            <button data-v="horizontal" class="${c.layout==='horizontal'?'on':''}">Horisontal</button>
          </div>
        </div>

        <div class="grid2">
          <div class="field">
            <span class="label">Kart</span>
            <div class="seg" id="show_map">
              <button data-v="off" class="${!c.show_map?'on':''}">Skjul</button>
              <button data-v="on" class="${c.show_map?'on':''}">Vis</button>
            </div>
          </div>
          <div class="field">
            <span class="label">Maks rader per liste</span>
            <input type="number" id="max_items" min="1" max="20"
              value="${c.max_items != null ? c.max_items : 5}">
          </div>
        </div>

        <div class="field">
          <span class="label">Seksjoner som vises</span>
          <div class="checks">${sectionRows}</div>
        </div>

        <label class="row">
          <input type="checkbox" id="show_empty" ${c.show_empty ? "checked" : ""}>
          <span>Vis tomme seksjoner (også når det ikke finnes data)</span>
        </label>
      </div>`;

    this._wire();
  }

  _wire() {
    const root = this.shadowRoot;
    const byId = id => root.getElementById(id);

    byId("entity") && byId("entity").addEventListener("change", e =>
      this._update("entity", e.target.value));
    byId("title") && byId("title").addEventListener("input", e =>
      this._update("title", e.target.value || undefined));
    byId("max_items") && byId("max_items").addEventListener("input", e =>
      this._update("max_items", parseInt(e.target.value, 10) || 5));
    byId("show_empty") && byId("show_empty").addEventListener("change", e =>
      this._update("show_empty", e.target.checked));

    root.querySelectorAll("#layout button").forEach(b =>
      b.addEventListener("click", () => this._update("layout", b.getAttribute("data-v"))));
    root.querySelectorAll("#show_map button").forEach(b =>
      b.addEventListener("click", () => this._update("show_map", b.getAttribute("data-v") === "on")));

    root.querySelectorAll("[data-section]").forEach(cb =>
      cb.addEventListener("change", () =>
        this._toggleSection(cb.getAttribute("data-section"), cb.checked)));
  }

  _esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
}

customElements.define("svv-traffic-card", SvvTrafficCard);
customElements.define("svv-traffic-card-editor", SvvTrafficCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "svv-traffic-card",
  name: "SVV Trafikk-kort",
  description: "Viser trafikkdata fra Statens vegvesen (veimeldinger, stengninger, trafikkmengde, kart, webkamera m.m.).",
  preview: true,
});

console.info("%c SVV-TRAFFIC-CARD %c v0.2.0 ",
  "background:#dc2626;color:#fff;border-radius:3px 0 0 3px;padding:2px 6px",
  "background:#334155;color:#fff;border-radius:0 3px 3px 0;padding:2px 6px");
