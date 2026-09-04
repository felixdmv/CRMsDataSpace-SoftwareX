import json
import re

INDEX_PATHS = [
    r"C:\Users\fdemiguel\OneDrive - Universidad de Burgos\Documentos\CRMsDataSpace\SoftwareX\code\static\index.html",
    r"C:\Users\fdemiguel\OneDrive - Universidad de Burgos\Documentos\CRMsDataSpace\geo-rag-explorer\index.html"
]

DATASET_PATH = r"C:\Users\fdemiguel\OneDrive - Universidad de Burgos\Documentos\CRMsDataSpace\SoftwareX\code\data\synthetic_escombreras_europe.json"

with open(DATASET_PATH, "r", encoding="utf-8") as f:
    raw_sites = json.load(f)

js_sites = []
for s in raw_sites:
    lat = s.get("latitude") or (float(s["location"].split(",")[0]) if s.get("location") else 40.0)
    lon = s.get("longitude") or (float(s["location"].split(",")[1]) if s.get("location") else 0.0)
    commodities = s.get("commodities", [])
    has_emerald = "lithium" in commodities or "cobalt" in commodities
    theme = "emerald" if has_emerald else "gold"
    status = s.get("project_status", "active")
    
    js_site = {
        "id": s.get("id"),
        "site_name": s.get("site_name"),
        "company": s.get("company", "EU Operator"),
        "country": s.get("country", "europe"),
        "country_name": s.get("country_name", "Europe"),
        "region": s.get("region_name", s.get("region", "Region")),
        "province": s.get("region_name", s.get("country_name", "EU")),
        "municipality": s.get("site_name"),
        "lat": lat,
        "lon": lon,
        "commodities": commodities,
        "commodities_label": s.get("commodities_label", ", ".join(commodities)),
        "facility_type": s.get("storage_facility_label", s.get("storage_facility_type", "Facility")),
        "material_type": s.get("material_type", "Tailings"),
        "project_status": status,
        "status_label": status.upper(),
        "status_color": "#10b981" if status == "active" else "#f59e0b",
        "area_m2": f"{s.get('tonnage_mt', 10)} MT",
        "description": s.get("description", ""),
        "environmental_flags": s.get("environmental_flags", []),
        "unfc_code": s.get("unfc_code", "UNFC E1-F2-G1"),
        "color_theme": theme
    }
    js_sites.append(js_site)

js_dataset_str = json.dumps(js_sites, indent=2, ensure_ascii=False)

FLOATING_MAP_FILTERS_HTML = """        <!-- Leaflet Map Area -->
        <div class="flex-1 relative border-b border-geodark-border overflow-hidden">
          <div id="map" class="w-full h-full bg-[#070a13]"></div>
          
          <!-- Floating Manual Filters Widget on Map Right Side -->
          <div class="absolute top-3 right-3 z-[1000] bg-slate-900/90 border border-slate-800/90 backdrop-blur-md rounded-xl p-3 shadow-2xl w-64 pointer-events-auto">
            <div class="flex items-center justify-between mb-2 pb-1.5 border-b border-slate-800">
              <span class="text-[10.5px] font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                🎛️ Filtros Manuales (Mapa)
              </span>
              <button type="button" onclick="resetManualFilters()" class="text-[9.5px] bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 px-2 py-0.5 rounded transition-all">
                Limpiar
              </button>
            </div>
            <div class="space-y-2 text-[10.5px]">
              <div>
                <label class="text-[9.5px] text-slate-400 font-semibold block mb-0.5">País (Europa):</label>
                <select id="manual-filter-country" onchange="applyManualFilters()" class="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 focus:border-emerald-500 focus:outline-none">
                  <option value="">Todos los Países</option>
                  <option value="spain">España</option>
                  <option value="germany">Alemania</option>
                  <option value="sweden">Suecia</option>
                  <option value="finland">Finlandia</option>
                  <option value="france">Francia</option>
                  <option value="portugal">Portugal</option>
                  <option value="austria">Austria</option>
                  <option value="poland">Polonia</option>
                  <option value="italy">Italia</option>
                  <option value="greece">Grecia</option>
                  <option value="ireland">Irlanda</option>
                  <option value="czechia">República Checa</option>
                </select>
              </div>
              <div>
                <label class="text-[9.5px] text-slate-400 font-semibold block mb-0.5">CRM Metal / Mineral:</label>
                <select id="manual-filter-commodity" onchange="applyManualFilters()" class="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 focus:border-emerald-500 focus:outline-none">
                  <option value="">Todos los Minerales</option>
                  <option value="lithium">Litio (Li)</option>
                  <option value="tungsten">Wolframio (W)</option>
                  <option value="copper">Cobre (Cu)</option>
                  <option value="cobalt">Cobalto (Co)</option>
                  <option value="rare earth elements">Tierras Raras (REE)</option>
                  <option value="tin">Estaño (Sn)</option>
                  <option value="nickel">Níquel (Ni)</option>
                  <option value="graphite">Grafito Natural</option>
                  <option value="titanium">Titanio (Ti)</option>
                </select>
              </div>
              <div>
                <label class="text-[9.5px] text-slate-400 font-semibold block mb-0.5">Tipo de Instalación:</label>
                <select id="manual-filter-facility" onchange="applyManualFilters()" class="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 focus:border-emerald-500 focus:outline-none">
                  <option value="">Todas las Instalaciones</option>
                  <option value="dump">Escombrera (Waste Dump)</option>
                  <option value="tailings">Balsa / TSF</option>
                  <option value="stockpile">Acopio de Minerales</option>
                  <option value="pond">Balsa de Decantación</option>
                </select>
              </div>
              <div>
                <label class="text-[9.5px] text-slate-400 font-semibold block mb-0.5">Estado Operativo:</label>
                <select id="manual-filter-status" onchange="applyManualFilters()" class="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 focus:border-emerald-500 focus:outline-none">
                  <option value="">Todos los Estados</option>
                  <option value="active">Activos</option>
                  <option value="inactive">Inactivos</option>
                  <option value="development">En Desarrollo</option>
                  <option value="care and maintenance">Mantenimiento</option>
                </select>
              </div>
            </div>
          </div>

          <!-- Map floating legend -->
          <div class="absolute bottom-3 left-3 bg-geodark-card/90 border border-geodark-border/80 backdrop-blur-md rounded-lg p-2.5 text-[11px] text-slate-300 z-[1000] shadow-xl pointer-events-auto">
            <h5 class="font-bold text-slate-200 mb-1.5 flex items-center gap-1">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
              </svg>
              Simbología de Minerales
            </h5>
            <div class="space-y-1">
              <div class="flex items-center gap-1.5">
                <span class="w-2.5 h-2.5 rounded-full bg-amber-500 border border-white inline-block"></span>
                <span>Wolframio / Estaño / Base (W, Sn)</span>
              </div>
              <div class="flex items-center gap-1.5">
                <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 border border-white inline-block"></span>
                <span>Litio / Cobalto (Li, Co)</span>
              </div>
            </div>
          </div>
        </div>"""

COMPLETE_JS_SCRIPT = """    // ==========================================
    // DATASET: 100 Synthetic European CRM Facilities
    // ==========================================
    let MINING_SITES = """ + js_dataset_str + """;

    let isTyping = false;
    let selectedSite = null;
    let markersMap = {};
    let mapInstance = null;
    let currentProvider = "mock";

    // ==========================================
    // MANUAL FILTERS ON MAP RIGHT SIDE
    // ==========================================
    function applyManualFilters() {
      const country = document.getElementById('manual-filter-country')?.value.toLowerCase() || '';
      const commodity = document.getElementById('manual-filter-commodity')?.value.toLowerCase() || '';
      const status = document.getElementById('manual-filter-status')?.value.toLowerCase() || '';
      const facility = document.getElementById('manual-filter-facility')?.value.toLowerCase() || '';

      const activeFilters = [];
      if (country) activeFilters.push({ label: 'País', values: [country] });
      if (commodity) activeFilters.push({ label: 'Mineral', values: [commodity] });
      if (status) activeFilters.push({ label: 'Estado', values: [status] });
      if (facility) activeFilters.push({ label: 'Instalación', values: [facility] });

      const matching = MINING_SITES.filter(s => {
        if (country && (s.country || '').toLowerCase() !== country) return false;
        if (commodity && !(s.commodities || []).some(c => c.toLowerCase().includes(commodity))) return false;
        if (status && (s.project_status || '').toLowerCase() !== status) return false;
        if (facility && !(s.facility_type || '').toLowerCase().includes(facility)) return false;
        return true;
      });

      renderMarkers(matching);
      updateActiveFilterBadges(activeFilters, matching.length);
    }

    function resetManualFilters() {
      ['country', 'commodity', 'status', 'facility'].forEach(id => {
        const el = document.getElementById(`manual-filter-${id}`);
        if (el) el.value = '';
      });
      renderMarkers(MINING_SITES);
      updateActiveFilterBadges([], MINING_SITES.length);
    }

    // ==========================================
    // HELPER FUNCTIONS FOR FORM & SELECTOR
    // ==========================================
    function changeLLMProvider(val) {
      setModelProvider(val);
    }

    function handleCustomSubmit(e) {
      if (e) {
        if (e.preventDefault) e.preventDefault();
        if (e.stopPropagation) e.stopPropagation();
      }
      sendChatMessage();
      return false;
    }

    function saveAPIKey() {
      const keyVal = document.getElementById('api-key-input')?.value;
      if (keyVal) {
        alert('API Key guardada correctamente para las consultas.');
      }
    }

    // ==========================================
    // INITIALIZATION & EVENT LISTENERS
    // ==========================================
    window.addEventListener('DOMContentLoaded', async () => {
      // 1. Initialize Leaflet Map centered on Europe
      initMap();
      
      // 2. Fetch European CRM sites from /api/sites backend if available
      try {
        const resp = await fetch('/api/sites');
        if (resp.ok) {
          const loadedSites = await resp.json();
          if (Array.isArray(loadedSites) && loadedSites.length > 0) {
            MINING_SITES = loadedSites.map(s => {
              const lat = s.latitude || (s.location ? parseFloat(s.location.split(',')[0]) : 50.0);
              const lon = s.longitude || (s.location ? parseFloat(s.location.split(',')[1]) : 10.0);
              return {
                id: s.id,
                site_name: s.site_name,
                company: s.company || 'EU Extractive Operator',
                country: s.country || 'europe',
                country_name: s.country_name || (s.country ? s.country.toUpperCase() : 'Europa'),
                region: s.region_name || s.region || 'Región UE',
                province: s.region_name || s.country_name || 'EU',
                municipality: s.site_name,
                lat: lat,
                lon: lon,
                commodities: s.commodities || [],
                commodities_label: s.commodities_label || (s.commodities ? s.commodities.join(', ') : 'CRM'),
                facility_type: s.storage_facility_label || s.storage_facility_type || 'Facility',
                material_type: s.material_type || 'Estériles y relaves',
                project_status: s.project_status || 'active',
                status_label: s.project_status ? s.project_status.toUpperCase() : 'ACTIVO',
                status_color: s.project_status === 'active' ? '#10b981' : '#f59e0b',
                area_m2: `${s.tonnage_mt || 10} MT de residuos`,
                description: s.description || 'Yacimiento de materias primas críticas registrado en el espacio de datos europeo.',
                environmental_flags: s.environmental_flags || [],
                unfc_code: s.unfc_code || 'UNFC E1-F2-G1',
                color_theme: s.commodities && (s.commodities.includes('lithium') || s.commodities.includes('cobalt')) ? 'emerald' : 'gold'
              };
            });
          }
        }
      } catch (err) {
        console.warn('Carga /api/sites omitida, usando dataset local de 100 sitios:', err);
      }

      // 3. Render Initial Markers across Europe
      renderMarkers();
      if (MINING_SITES.length > 0) {
        selectSite(MINING_SITES[0].id);
      }

      // 4. Setup chat input listener (Enter key)
      const getInput = () => document.getElementById('chat-input') || document.getElementById('custom-input');
      const inputEl = getInput();
      if (inputEl) {
        inputEl.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            e.stopPropagation();
            sendChatMessage();
          }
        });
      }
    });

    // ==========================================
    // MAP FUNCTIONS (Leaflet.js Engine)
    // ==========================================
    function initMap() {
      const mapContainer = document.getElementById('map');
      if (!mapContainer) return;

      mapInstance = L.map('map', {
        center: [51.1657, 10.4515], // Center of Europe (Germany/Czechia coordinates)
        zoom: 4,
        zoomControl: false,
        attributionControl: false
      });

      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 20,
        subdomains: 'abcd'
      }).addTo(mapInstance);

      L.control.attribution({
        position: 'bottomright',
        prefix: 'Leaflet.js Engine | CartoDB Dark (OpenStreetMap)'
      }).addTo(mapInstance);

      L.control.zoom({
        position: 'topright'
      }).addTo(mapInstance);
    }

    function renderMarkers(sitesToHighlight = null) {
      if (!mapInstance) return;

      // Clear existing markers
      Object.values(markersMap).forEach(m => m.remove());
      markersMap = {};

      const highlightGroup = [];

      MINING_SITES.forEach(site => {
        const isMatched = !sitesToHighlight || sitesToHighlight.some(s => s.id === site.id);
        const opacity = isMatched ? 1.0 : 0.25;

        let color = '#10b981'; // Emerald
        let pulseClass = isMatched ? 'marker-pulse-emerald' : '';
        if (site.color_theme === 'gold') {
          color = '#fbbf24'; // Gold
          if (isMatched) pulseClass = 'marker-pulse-gold';
        }

        const isSelected = selectedSite && selectedSite.id === site.id;
        const size = isSelected ? 16 : (isMatched ? 12 : 9);
        const borderSize = isSelected ? 3 : 2;

        const customIcon = L.divIcon({
          className: 'custom-leaflet-marker',
          html: `<div class="${pulseClass}" style="
            width: ${size}px; 
            height: ${size}px; 
            background-color: ${color}; 
            border: ${borderSize}px solid #0f172a; 
            border-radius: 50%; 
            opacity: ${opacity};
            cursor: pointer;
            box-shadow: 0 0 10px ${color}88;
          "></div>`,
          iconSize: [size, size],
          iconAnchor: [size / 2, size / 2]
        });

        const marker = L.marker([site.lat, site.lon], { icon: customIcon }).addTo(mapInstance);
        
        // Popup metadata card
        const popupHtml = `
          <div style="font-family: system-ui, sans-serif; padding: 4px; color: #0f172a;">
            <div style="font-weight: bold; font-size: 13px; color: #047857; margin-bottom: 2px;">${site.site_name}</div>
            <div style="font-size: 11px; color: #475569; margin-bottom: 4px;">📍 ${site.country_name} (${site.region})</div>
            <div style="font-size: 11px; margin-bottom: 4px;"><strong>Minerales:</strong> ${site.commodities_label}</div>
            <div style="font-size: 10px; padding: 2px 6px; background: #e2e8f0; border-radius: 4px; display: inline-block;">${site.facility_type}</div>
            <button onclick="selectSite('${site.id}', true)" style="margin-top: 8px; width: 100%; padding: 4px; background: #047857; color: white; border: none; border-radius: 4px; font-size: 11px; font-weight: bold; cursor: pointer;">Ver Detalles</button>
          </div>
        `;
        marker.bindPopup(popupHtml);

        marker.on('click', () => {
          selectSite(site.id, true);
        });

        markersMap[site.id] = marker;

        if (isMatched) {
          highlightGroup.push([site.lat, site.lon]);
        }
      });

      // Fit map bounds to matching markers if filtered
      if (sitesToHighlight && highlightGroup.length > 0) {
        try {
          const bounds = L.latLngBounds(highlightGroup);
          mapInstance.fitBounds(bounds, { padding: [40, 40], maxZoom: 8 });
        } catch (e) {
          console.warn('Could not fit bounds:', e);
        }
      }
    }

    function selectSite(siteId, flyTo = false) {
      const site = MINING_SITES.find(s => s.id === siteId);
      if (!site) return;

      selectedSite = site;

      // Update Detail Card on Left UI Panel
      const nameEl = document.getElementById('site-name');
      const companyEl = document.getElementById('site-company');
      const regionEl = document.getElementById('site-region');
      const commoditiesEl = document.getElementById('site-commodities');
      const typeEl = document.getElementById('site-facility-type');
      const statusEl = document.getElementById('site-status');
      const unfcEl = document.getElementById('site-unfc');
      const descEl = document.getElementById('site-description');

      if (nameEl) nameEl.textContent = site.site_name;
      if (companyEl) companyEl.textContent = site.company;
      if (regionEl) regionEl.textContent = `${site.region}, ${site.country_name}`;
      if (commoditiesEl) commoditiesEl.textContent = site.commodities_label;
      if (typeEl) typeEl.textContent = site.facility_type;
      if (statusEl) {
        statusEl.textContent = site.status_label;
        statusEl.style.backgroundColor = site.status_color + '22';
        statusEl.style.color = site.status_color;
        statusEl.style.borderColor = site.status_color + '44';
      }
      if (unfcEl) unfcEl.textContent = site.unfc_code;
      if (descEl) descEl.textContent = site.description;

      // Fly to site location on Leaflet map if requested
      if (flyTo && mapInstance) {
        mapInstance.flyTo([site.lat, site.lon], 7, { duration: 1.2 });
        if (markersMap[site.id]) {
          markersMap[site.id].openPopup();
        }
      }
    }

    // ==========================================
    // SCENARIOS & CHAT LOGIC
    // ==========================================
    function setModelProvider(provider) {
      currentProvider = provider;
      const indicator = document.getElementById('current-model-indicator');
      if (indicator) {
        if (provider === 'gemini') {
          indicator.textContent = 'Gemini 1.5 Pro';
        } else if (provider === 'openai') {
          indicator.textContent = 'OpenAI GPT-4o';
        } else {
          indicator.textContent = 'Standalone Mock Engine';
        }
      }

      const apiKeyContainer = document.getElementById('api-key-container');
      if (apiKeyContainer) {
        if (provider === 'gemini' || provider === 'openai') {
          apiKeyContainer.classList.remove('hidden');
        } else {
          apiKeyContainer.classList.add('hidden');
        }
      }
    }

    function runScenario(scenarioId) {
      let query = "";
      if (scenarioId === 'query_1') {
        query = "Muestra escombreras de litio y cobalto en España y Finlandia que estén activas";
      } else if (scenarioId === 'query_2') {
        query = "Balsas de wolframio sin restaurar en Alemania";
      } else if (scenarioId === 'query_3') {
        query = "Depósitos de tierras raras en Suecia y Francia";
      }

      const getInput = () => document.getElementById('chat-input') || document.getElementById('custom-input');
      const inputEl = getInput();
      if (inputEl) {
        inputEl.value = query;
      }
      sendChatMessage(query);
    }

    async function sendChatMessage(overrideQuery = null) {
      if (isTyping) return;

      const getInput = () => document.getElementById('chat-input') || document.getElementById('custom-input');
      const inputEl = getInput();
      const query = overrideQuery || (inputEl ? inputEl.value.trim() : '');
      if (!query) return;

      if (inputEl && !overrideQuery) inputEl.value = '';

      const chatContainer = document.getElementById('chat-messages');
      if (!chatContainer) return;

      // 1. Append User Message Bubble
      const userBubble = document.createElement('div');
      userBubble.className = 'flex justify-end mb-3';
      userBubble.innerHTML = `
        <div class="max-w-[85%] bg-emerald-600 text-white text-xs px-3.5 py-2.5 rounded-xl rounded-tr-none shadow-md">
          <p class="font-medium">${escapeHtml(query)}</p>
        </div>
      `;
      chatContainer.appendChild(userBubble);
      chatContainer.scrollTop = chatContainer.scrollHeight;

      // 2. Append Typing Indicator
      isTyping = true;
      const typingBubble = document.createElement('div');
      typingBubble.id = 'typing-indicator';
      typingBubble.className = 'flex justify-start mb-3';
      typingBubble.innerHTML = `
        <div class="bg-slate-900 border border-slate-800 text-slate-300 text-xs px-3.5 py-2.5 rounded-xl rounded-tl-none flex items-center gap-2">
          <span class="animate-pulse font-mono text-emerald-400">Procesando consulta NLU + Solr...</span>
        </div>
      `;
      chatContainer.appendChild(typingBubble);
      chatContainer.scrollTop = chatContainer.scrollHeight;

      // 3. Send Request to REST Server (/api/chat)
      try {
        const apiKey = document.getElementById('api-key-input')?.value || '';
        const resp = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: query, query: query, provider: currentProvider, api_key: apiKey })
        });

        const data = await resp.json();
        
        // Remove typing indicator
        const typEl = document.getElementById('typing-indicator');
        if (typEl) typEl.remove();

        // 4. Append Assistant Response Bubble
        const assistantBubble = document.createElement('div');
        assistantBubble.className = 'flex justify-start mb-4';
        
        let narrativeHtml = data.narrative || data.response_text || "Consulta procesada con éxito.";
        narrativeHtml = formatMarkdownText(narrativeHtml);

        let evidencesHtml = "";
        if (data.evidences && data.evidences.length > 0) {
          evidencesHtml = `<div class="mt-3 pt-3 border-t border-slate-800"><div class="text-[10px] text-amber-400 font-bold uppercase tracking-wider mb-2">📄 Evidencias Técnicas extraídas de PDFs:</div>`;
          data.evidences.forEach(ev => {
            evidencesHtml += `
              <div class="bg-slate-950 p-2 rounded border border-slate-800/80 mb-2 text-[11px]">
                <div class="font-bold text-slate-200">${escapeHtml(ev.title)} (Pág. ${ev.page})</div>
                <div class="text-slate-400 text-[10px] my-1">${escapeHtml(ev.snippet)}</div>
                <div class="flex gap-1 flex-wrap">${(ev.entities || []).map(ent => `<span class="bg-emerald-950/60 text-emerald-400 border border-emerald-900/60 px-1.5 py-0.5 rounded text-[9px]">${escapeHtml(ent)}</span>`).join('')}</div>
              </div>
            `;
          });
          evidencesHtml += `</div>`;
        }

        assistantBubble.innerHTML = `
          <div class="max-w-[90%] bg-slate-900 border border-slate-800 text-slate-200 text-xs px-4 py-3 rounded-xl rounded-tl-none shadow-lg">
            <div class="prose prose-invert text-xs leading-relaxed">${narrativeHtml}</div>
            ${evidencesHtml}
          </div>
        `;
        chatContainer.appendChild(assistantBubble);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        // 5. Update Map Markers & Highlighting
        const matchedIds = data.matched_ids || [];
        const matchingSites = MINING_SITES.filter(s => matchedIds.includes(s.id));
        renderMarkers(matchingSites.length > 0 ? matchingSites : MINING_SITES);

        // 6. Update Active Map Filter Badges over Map Header
        updateActiveFilterBadges(data.active_map_filters || [], matchedIds.length);

        // 7. Update Solr Engine Inspector Panel
        updateInspectorDisplay(data);

      } catch (err) {
        console.error('API Error:', err);
        const typEl = document.getElementById('typing-indicator');
        if (typEl) typEl.remove();

        const errBubble = document.createElement('div');
        errBubble.className = 'flex justify-start mb-3';
        errBubble.innerHTML = `
          <div class="bg-red-950/60 border border-red-900/60 text-red-300 text-xs px-3.5 py-2.5 rounded-xl">
            Error al conectar con el servidor: ${escapeHtml(err.message)}
          </div>
        `;
        chatContainer.appendChild(errBubble);
      } finally {
        isTyping = false;
      }
    }

    function updateActiveFilterBadges(activeFilters = [], matchedCount = 0) {
      const container = document.getElementById('active-filters-badges');
      const counter = document.getElementById('site-counter-display');

      if (counter) {
        counter.textContent = `Mostrando ${matchedCount > 0 ? matchedCount : MINING_SITES.length} / ${MINING_SITES.length} Instalaciones Europeas`;
      }

      if (!container) return;
      container.innerHTML = '';

      if (!activeFilters || activeFilters.length === 0) {
        container.innerHTML = '<span class="text-slate-500 text-[10px] italic">Sin filtros activos (Mostrando Europa completa)</span>';
        return;
      }

      activeFilters.forEach(f => {
        const badge = document.createElement('div');
        badge.className = 'flex items-center gap-1.5 bg-emerald-950/70 border border-emerald-800/80 text-emerald-300 text-[10px] px-2.5 py-1 rounded-md shadow-sm font-mono';
        badge.innerHTML = `<span class="font-bold text-amber-400">${escapeHtml(f.label)}:</span> <span>${escapeHtml(Array.isArray(f.values) ? f.values.join(', ') : f.values)}</span>`;
        container.appendChild(badge);
      });
    }

    function updateInspectorDisplay(data = null) {
      const solrQueryCode = document.getElementById('inspector-query-code');
      const facetsCode = document.getElementById('inspector-facets-code');
      const nerCode = document.getElementById('inspector-ner-code');

      if (data) {
        if (solrQueryCode) solrQueryCode.textContent = JSON.stringify(data.solr_query || {}, null, 2);
        if (facetsCode) facetsCode.textContent = JSON.stringify(data.solr_facets || {}, null, 2);
        if (nerCode) nerCode.textContent = JSON.stringify(data.ner_entities || data.extracted_json || {}, null, 2);
      }
    }

    function toggleBottomPanel() {
      const panel = document.getElementById('bottom-inspector-panel');
      if (!panel) return;
      if (panel.classList.contains('h-10')) {
        panel.classList.remove('h-10');
        panel.classList.add('h-64');
      } else {
        panel.classList.remove('h-64');
        panel.classList.add('h-10');
      }
    }

    function switchInspectorTab(tabName) {
      const tabs = ['query', 'facets', 'ner'];
      tabs.forEach(t => {
        const btn = document.getElementById(`tab-${t}`);
        const content = document.getElementById(`inspector-${t}-content`);
        if (btn && content) {
          if (t === tabName) {
            btn.className = 'px-3 py-1 rounded text-[10px] font-semibold transition-all bg-slate-800 text-emerald-400';
            content.classList.remove('hidden');
          } else {
            btn.className = 'px-3 py-1 rounded text-[10px] font-semibold transition-all text-slate-400 hover:text-slate-200';
            content.classList.add('hidden');
          }
        }
      });
    }

    function formatMarkdownText(text) {
      if (!text) return '';
      return text
        .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
        .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
        .replace(/\\n/g, '<br/>');
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
    }
  </script>
</body>
</html>"""

for path in INDEX_PATHS:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove old manual filter bar from left panel if present
    content = re.sub(
        r'<!-- Manual Filters Interactive Bar -->\s*<div class="p-2\.5 bg-\[#0e1424\].*?</div>\s*</div>',
        '',
        content,
        flags=re.DOTALL
    )

    # Replace Leaflet Map section with floating manual filter widget on the right side
    map_section_start = content.find("<!-- Leaflet Map Area -->")
    if map_section_start != -1:
        map_section_end = content.find("<!-- Technical Information panel", map_section_start)
        if map_section_end != -1:
            content = content[:map_section_start] + FLOATING_MAP_FILTERS_HTML + "\n\n        " + content[map_section_end:]

    # Inject JS logic
    script_start = content.find("<!-- ==========================================\n      JAVASCRIPT LOGIC (PURE VANILLA)\n      ========================================== -->\n  <script>")
    if script_start == -1:
        script_start = content.find("<script>")

    if script_start != -1:
        header_html = content[:script_start]
        final_html = header_html + "<!-- ==========================================\n      JAVASCRIPT LOGIC (PURE VANILLA)\n      ========================================== -->\n  <script>\n" + COMPLETE_JS_SCRIPT
        with open(path, "w", encoding="utf-8") as f:
            f.write(final_html)
        print(f"Successfully placed floating manual filters on map right side in: {path}")
    else:
        print(f"Error: <script> tag not found in {path}")
