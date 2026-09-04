import json
import os
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

HTML_FULL_ENGLISH = """<!DOCTYPE html>
<html lang="en" class="h-full bg-slate-950">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CRMsDataSpace Explorer — Conversational NLU & GIS Spatial Search</title>
  <meta name="description" content="SoftwareX demonstrator: Decoupled NLU-Solr software architecture with Leaflet.js GIS map visual synchronization for Critical Raw Materials data spaces.">

  <!-- Favicon -->
  <link rel="icon" href="/favicon.ico" type="image/x-icon">

  <!-- Google Fonts: Inter -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">

  <!-- Leaflet.js CSS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="" />

  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          fontFamily: {
            sans: ['Inter', 'sans-serif'],
            mono: ['JetBrains Mono', 'monospace'],
          },
          colors: {
            geodark: {
              bg: '#0a0d18',
              card: '#0f1424',
              border: '#1e293b',
              accent: '#059669',
            }
          }
        }
      }
    }
  </script>

  <style>
    /* Custom Scrollbars */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0a0d18; }
    ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #334155; }

    /* Map Marker Pulse Animation */
    @keyframes marker-pulse-emerald {
      0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
      70% { box-shadow: 0 0 0 12px rgba(16, 185, 129, 0); }
      100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    @keyframes marker-pulse-gold {
      0% { box-shadow: 0 0 0 0 rgba(251, 191, 36, 0.7); }
      70% { box-shadow: 0 0 0 12px rgba(251, 191, 36, 0); }
      100% { box-shadow: 0 0 0 0 rgba(251, 191, 36, 0); }
    }
    .marker-pulse-emerald { animation: marker-pulse-emerald 2s infinite; }
    .marker-pulse-gold { animation: marker-pulse-gold 2s infinite; }
    .leaflet-container { background: #070a13 !important; }
  </style>
</head>
<body class="h-full flex flex-col font-sans text-slate-100 bg-[#060811] antialiased select-none">

  <!-- ==========================================
      HEADER BAR
      ========================================== -->
  <header class="h-14 bg-[#0a0e1c] border-b border-geodark-border px-4 flex items-center justify-between shrink-0 shadow-md relative z-20">
    <div class="flex items-center gap-3">
      <div class="w-8 h-8 rounded-lg bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-between p-1.5 shadow-sm">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 002 2h1.5a2.5 2.5 0 002.5-2.5V11a2 2 0 012-2h1.065M12 2a10 10 0 100 20 10 10 0 000-20z" />
        </svg>
      </div>
      <div>
        <h1 class="font-bold text-sm text-slate-100 tracking-wide flex items-center gap-2">
          CRMsDataSpace Explorer
          <span class="text-[10px] font-mono font-normal bg-emerald-950 text-emerald-400 border border-emerald-800/80 px-2 py-0.5 rounded">
            SoftwareX Reference Architecture v1.0.0
          </span>
        </h1>
        <p class="text-[10.5px] text-slate-400 font-medium">Conversational NLU & Solr Spatial Filtering for European Critical Raw Materials</p>
      </div>
    </div>

    <!-- Active Filter Badges over Map Header -->
    <div id="active-filters-container" class="hidden md:flex items-center gap-2 bg-slate-950/80 border border-slate-800/80 px-3 py-1.5 rounded-lg max-w-xl">
      <span class="text-[10px] text-slate-400 uppercase tracking-widest font-semibold shrink-0">Active GIS Filters:</span>
      <div id="active-filters-badges" class="flex items-center gap-1.5 overflow-x-auto text-[10.5px]">
        <span class="text-slate-500 italic text-[10px]">No active filters (Showing full European Data Space)</span>
      </div>
    </div>

    <div class="flex items-center gap-3">
      <div id="site-counter-display" class="text-[11px] font-mono font-semibold text-emerald-400 bg-emerald-950/50 border border-emerald-900/50 px-3 py-1.5 rounded-md hidden sm:block">
        Showing 100 / 100 European Sites
      </div>
      
      <div class="flex items-center gap-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-md">
        <span class="relative flex h-2 w-2">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
        </span>
        <span class="text-slate-400 text-[10px]">Mode:</span>
        <span id="current-model-indicator" class="text-emerald-400 font-bold text-[10px] uppercase">Standalone Engine</span>
      </div>
    </div>
  </header>

  <!-- ==========================================
      MAIN CONTENT CONTAINER
      ========================================== -->
  <main class="flex-1 flex flex-col overflow-hidden relative">
    
    <!-- Middle: Horizontal split Panels (Chat | Map & Technical) -->
    <div class="flex-1 flex flex-row overflow-hidden">
      
      <!-- ==========================================
          LEFT PANEL: CHAT & EVIDENCES (50%)
          ========================================== -->
      <section class="w-1/2 h-full flex flex-col border-r border-geodark-border bg-[#0a0d18] relative z-10">
        
        <!-- Reviewer Test Bench Bar -->
        <div class="p-3 bg-[#0d1222] border-b border-geodark-border flex flex-col gap-1.5 shadow-sm">
          <div class="text-[10px] text-slate-400 uppercase tracking-widest font-semibold flex items-center gap-1.5">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            Reviewer Test Bench (Preset Benchmark Queries)
          </div>
          
          <div class="grid grid-cols-3 gap-2">
            <button 
              id="btn-scenario-1"
              onclick="runScenario('query_1')"
              class="text-left p-2 rounded-lg border text-[11px] leading-tight transition-all flex flex-col justify-between bg-geodark-card border-geodark-border hover:border-slate-600 text-slate-300"
            >
              <span class="font-semibold block text-emerald-400 mb-1">Test 1: Active Li & Co</span>
              <span class="text-slate-400 text-[10px]">Lithium and Cobalt active sites in Spain & Finland</span>
            </button>
            
            <button 
              id="btn-scenario-2"
              onclick="runScenario('query_2')"
              class="text-left p-2 rounded-lg border text-[11px] leading-tight transition-all flex flex-col justify-between bg-geodark-card border-geodark-border hover:border-slate-600 text-slate-300"
            >
              <span class="font-semibold block text-amber-400 mb-1">Test 2: Tungsten Ponds</span>
              <span class="text-slate-400 text-[10px]">Unrestored tungsten ponds in Germany</span>
            </button>

            <button 
              id="btn-scenario-3"
              onclick="runScenario('query_3')"
              class="text-left p-2 rounded-lg border text-[11px] leading-tight transition-all flex flex-col justify-between bg-geodark-card border-geodark-border hover:border-slate-600 text-slate-300"
            >
              <span class="font-semibold block text-blue-400 mb-1">Test 3: REE Deposits</span>
              <span class="text-slate-400 text-[10px]">Rare Earth Elements in Sweden & France</span>
            </button>
          </div>
        </div>

        <!-- Chat Feed Window -->
        <div id="chat-messages" class="flex-1 overflow-y-auto p-4 space-y-4 bg-[#080b14]">
          
          <!-- Welcome Message -->
          <div class="flex justify-start mb-4">
            <div class="max-w-[90%] bg-slate-900 border border-slate-800 text-slate-200 text-xs px-4 py-3 rounded-xl rounded-tl-none shadow-lg">
              <div class="font-bold text-emerald-400 text-xs mb-1">👋 Welcome to CRMsDataSpace Explorer</div>
              <p class="text-slate-300 leading-relaxed">
                This conversational assistant allows domain experts and scientific reviewers to query the European Critical Raw Materials Data Space using natural language.
              </p>
              <div class="mt-2.5 pt-2.5 border-t border-slate-800/80 text-[11px] text-slate-400">
                <span class="font-semibold text-slate-200">Try asking:</span>
                <ul class="list-disc list-inside mt-1 space-y-0.5 text-emerald-300 font-mono text-[10.5px]">
                  <li>"Show active lithium and cobalt waste dumps in Spain and Finland"</li>
                  <li>"Unrestored tungsten tailings ponds in Germany"</li>
                  <li>"Rare Earth Elements (REE) facilities in Sweden"</li>
                </ul>
              </div>
            </div>
          </div>

        </div>

        <!-- Input Bar with integrated LLM Provider Selector right next to query box -->
        <form onsubmit="event.preventDefault(); handleCustomSubmit(event); return false;" class="p-3 bg-[#0d1222] border-t border-geodark-border flex flex-col gap-2 shrink-0 z-10">
          <div class="flex items-center gap-2 w-full">
            <!-- LLM Provider Selector -->
            <select 
              id="llm-provider-select" 
              onchange="changeLLMProvider(this.value)" 
              class="bg-slate-950 border border-emerald-500/80 hover:border-emerald-400 text-emerald-400 font-bold text-[11px] px-2 py-2 rounded-lg focus:outline-none cursor-pointer transition-all shadow-md shrink-0"
              title="Execution Engine Mode"
            >
              <option value="rules">⚡ Standalone Engine (Mock)</option>
              <option value="gemini">✨ Gemini 1.5 Flash / Pro</option>
              <option value="openai">🤖 OpenAI GPT-4o</option>
            </select>

            <input 
              type="text" 
              id="chat-input"
              placeholder="Enter spatial query (e.g. 'Active lithium tailings in Spain & Finland')..." 
              class="flex-1 bg-slate-950 border border-geodark-border rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500/80"
            />

            <button type="button" onclick="sendChatMessage()" class="bg-emerald-600 hover:bg-emerald-500 border border-emerald-500/20 text-white font-medium text-xs px-4 py-2 rounded-lg transition-all flex items-center gap-1.5 shrink-0"
            >
              <span>Send</span>
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </button>
          </div>

          <!-- API Key Input Field (Hidden by default in Standalone Mode) -->
          <div id="api-key-container" class="hidden flex items-center gap-2 bg-slate-950 p-2 border border-slate-800 rounded-lg">
            <span class="text-[10px] text-amber-400 font-semibold shrink-0">API Key:</span>
            <input 
              type="password" 
              id="api-key-input" 
              placeholder="Enter optional Gemini / OpenAI API Key..." 
              class="flex-1 bg-slate-900 border border-slate-700 rounded px-2.5 py-1 text-[10.5px] text-slate-200 focus:border-emerald-500 focus:outline-none" 
            />
            <button type="button" onclick="saveAPIKey()" class="bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-[10px] px-3 py-1 rounded transition-all shrink-0">
              Save Key
            </button>
          </div>
        </form>

      </section>

      <!-- ==========================================
          RIGHT PANEL: MAP & INFORMATION (50%)
          ========================================== -->
      <section class="w-1/2 h-full flex flex-col relative">
        
        <!-- Leaflet Map Area -->
        <div class="flex-1 relative border-b border-geodark-border overflow-hidden">
          <div id="map" class="w-full h-full bg-[#070a13]"></div>
          
          <!-- Floating Manual Filters Widget on Map Right Side -->
          <div class="absolute top-3 right-3 z-[1000] bg-slate-900/90 border border-slate-800/90 backdrop-blur-md rounded-xl p-3 shadow-2xl w-64 pointer-events-auto">
            <div class="flex items-center justify-between mb-2 pb-1.5 border-b border-slate-800">
              <span class="text-[10.5px] font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                🎛️ Spatial & Attribute Filters
              </span>
              <button type="button" onclick="resetManualFilters()" class="text-[9.5px] bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 px-2 py-0.5 rounded transition-all">
                Reset
              </button>
            </div>
            <div class="space-y-2 text-[10.5px]">
              <div>
                <label class="text-[9.5px] text-slate-400 font-semibold block mb-0.5">Country (Europe):</label>
                <select id="manual-filter-country" onchange="applyManualFilters()" class="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 focus:border-emerald-500 focus:outline-none">
                  <option value="">All European Countries</option>
                  <option value="spain">Spain</option>
                  <option value="germany">Germany</option>
                  <option value="sweden">Sweden</option>
                  <option value="finland">Finland</option>
                  <option value="france">France</option>
                  <option value="portugal">Portugal</option>
                  <option value="austria">Austria</option>
                  <option value="poland">Poland</option>
                  <option value="italy">Italy</option>
                  <option value="greece">Greece</option>
                  <option value="ireland">Ireland</option>
                  <option value="czechia">Czechia</option>
                </select>
              </div>
              <div>
                <label class="text-[9.5px] text-slate-400 font-semibold block mb-0.5">CRM Metal / Commodity:</label>
                <select id="manual-filter-commodity" onchange="applyManualFilters()" class="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 focus:border-emerald-500 focus:outline-none">
                  <option value="">All Critical Raw Materials</option>
                  <option value="lithium">Lithium (Li)</option>
                  <option value="tungsten">Tungsten / Wolfram (W)</option>
                  <option value="copper">Copper (Cu)</option>
                  <option value="cobalt">Cobalt (Co)</option>
                  <option value="rare earth elements">Rare Earth Elements (REE)</option>
                  <option value="tin">Tin (Sn)</option>
                  <option value="nickel">Nickel (Ni)</option>
                  <option value="graphite">Natural Graphite</option>
                  <option value="titanium">Titanium (Ti)</option>
                </select>
              </div>
              <div>
                <label class="text-[9.5px] text-slate-400 font-semibold block mb-0.5">Storage Facility Type:</label>
                <select id="manual-filter-facility" onchange="applyManualFilters()" class="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 focus:border-emerald-500 focus:outline-none">
                  <option value="">All Facility Types</option>
                  <option value="dump">Waste Dump</option>
                  <option value="tailings">Tailings Storage Facility (TSF)</option>
                  <option value="stockpile">Mineral Stockpile</option>
                  <option value="pond">Settling Pond</option>
                </select>
              </div>
              <div>
                <label class="text-[9.5px] text-slate-400 font-semibold block mb-0.5">Operational Status:</label>
                <select id="manual-filter-status" onchange="applyManualFilters()" class="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 focus:border-emerald-500 focus:outline-none">
                  <option value="">All Statuses</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="development">Under Development</option>
                  <option value="care and maintenance">Care & Maintenance</option>
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
              CRM Category Legend
            </h5>
            <div class="space-y-1">
              <div class="flex items-center gap-1.5">
                <span class="w-2.5 h-2.5 rounded-full bg-amber-500 border border-white inline-block"></span>
                <span>Tungsten / Tin / Base (W, Sn)</span>
              </div>
              <div class="flex items-center gap-1.5">
                <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 border border-white inline-block"></span>
                <span>Battery Metals (Lithium, Cobalt)</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Technical Information Panel (Selected Facility Specifications) -->
        <div id="ficha-container" class="h-[235px] bg-[#090d15] p-3.5 overflow-y-auto shrink-0 flex flex-col border-t border-geodark-border shadow-inner">
          <div class="flex items-center justify-between mb-2 pb-1.5 border-b border-slate-800">
            <h3 id="site-name" class="font-bold text-sm text-emerald-400">Select a facility marker on the map</h3>
            <span id="site-status" class="text-[10px] font-mono px-2 py-0.5 rounded border border-emerald-800 text-emerald-400 bg-emerald-950">ACTIVE</span>
          </div>
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-2 text-[11px] mb-2.5">
            <div><span class="text-slate-400 block text-[9.5px]">Operator:</span><span id="site-company" class="font-medium text-slate-200">EU Operator</span></div>
            <div><span class="text-slate-400 block text-[9.5px]">Location:</span><span id="site-region" class="font-medium text-slate-200">Europe</span></div>
            <div><span class="text-slate-400 block text-[9.5px]">Commodities:</span><span id="site-commodities" class="font-medium text-amber-300">Lithium, Cobalt</span></div>
            <div><span class="text-slate-400 block text-[9.5px]">UNFC Code:</span><span id="site-unfc" class="font-mono text-emerald-400">UNFC E1-F2-G1</span></div>
          </div>
          <div class="text-[11px] text-slate-300 leading-relaxed">
            <span class="text-slate-400 block text-[9.5px] mb-0.5">Technical Overview:</span>
            <p id="site-description" class="text-slate-300">Click any site marker on the interactive Europe map to view detailed facility specifications, UNFC classifications, and geo-environmental flags.</p>
          </div>
        </div>

      </section>

    </div>

    <!-- ==========================================
        BOTTOM PANEL: APACHE SOLR ENGINE INSPECTOR
        ========================================== -->
    <div id="bottom-panel" class="border-t border-geodark-border transition-all duration-300 relative bg-[#070a12] flex flex-col shrink-0 h-[250px]">
      
      <!-- Drawer Header Bar -->
      <div 
        onclick="toggleBottomPanel()"
        class="h-9 bg-[#0b0e1b] px-4 flex items-center justify-between cursor-pointer border-b border-geodark-border hover:bg-slate-900/80 transition-all select-none"
      >
        <div class="flex items-center gap-2 text-xs">
          <span class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
          </span>
          <span class="font-bold text-slate-200 flex items-center gap-2">
            Apache Solr Engine Inspector 
            <span class="text-[10px] font-normal text-slate-500 font-mono">
              (NLU Pipeline & Search Audit Drawer)
            </span>
          </span>
        </div>

        <div class="flex items-center gap-4">
          <!-- Inspector Tabs -->
          <div id="inspector-tabs" class="flex bg-slate-950 p-0.5 rounded border border-slate-800" onclick="event.stopPropagation()">
            <button 
              type="button"
              id="tab-query"
              onclick="switchInspectorTab('query')"
              class="px-3 py-1 rounded text-[10px] font-semibold transition-all bg-slate-800 text-emerald-400"
            >
              Solr Query Syntax (q, fq)
            </button>
            <button 
              type="button"
              id="tab-facets"
              onclick="switchInspectorTab('facets')"
              class="px-3 py-1 rounded text-[10px] font-semibold transition-all text-slate-400 hover:text-slate-200"
            >
              Facet Counts
            </button>
            <button 
              type="button"
              id="tab-ner"
              onclick="switchInspectorTab('ner')"
              class="px-3 py-1 rounded text-[10px] font-semibold transition-all text-slate-400 hover:text-slate-200"
            >
              NLU Extracted JSON
            </button>
          </div>
        </div>
      </div>

      <!-- Drawer Content -->
      <div class="flex-1 p-3 overflow-y-auto font-mono text-xs">
        <div id="inspector-query-content" class="h-full">
          <pre id="inspector-query-code" class="text-amber-300 text-[11px] leading-relaxed">{\n  "info": "Submit a conversational query above or click a preset test case to inspect generated Apache Solr search parameters."\n}</pre>
        </div>

        <div id="inspector-facets-content" class="h-full hidden">
          <pre id="inspector-facets-code" class="text-emerald-300 text-[11px] leading-relaxed">{\n  "info": "Facet distributions (country counts, commodity breakdown, status) will be displayed here."\n}</pre>
        </div>

        <div id="inspector-ner-content" class="h-full hidden">
          <pre id="inspector-ner-code" class="text-blue-300 text-[11px] leading-relaxed">{\n  "info": "Structured JSON contract extracted by Dual-Variant NLU Engine (v1 Few-Shot / v3 OpenAPI Schema)."\n}</pre>
        </div>
      </div>

    </div>

  </main>

  <!-- Leaflet JS -->
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>

  <!-- ==========================================
      JAVASCRIPT LOGIC (PURE VANILLA)
      ========================================== -->
  <script>
    // ==========================================
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
      if (country) activeFilters.push({ label: 'Country', values: [country] });
      if (commodity) activeFilters.push({ label: 'Commodity', values: [commodity] });
      if (status) activeFilters.push({ label: 'Status', values: [status] });
      if (facility) activeFilters.push({ label: 'Facility', values: [facility] });

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
        alert('API Key saved successfully for session requests.');
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
                country_name: s.country_name || (s.country ? s.country.toUpperCase() : 'Europe'),
                region: s.region_name || s.region || 'EU Region',
                province: s.region_name || s.country_name || 'EU',
                municipality: s.site_name,
                lat: lat,
                lon: lon,
                commodities: s.commodities || [],
                commodities_label: s.commodities_label || (s.commodities ? s.commodities.join(', ') : 'CRM'),
                facility_type: s.storage_facility_label || s.storage_facility_type || 'Facility',
                material_type: s.material_type || 'Tailings & Waste',
                project_status: s.project_status || 'active',
                status_label: s.project_status ? s.project_status.toUpperCase() : 'ACTIVE',
                status_color: s.project_status === 'active' ? '#10b981' : '#f59e0b',
                area_m2: `${s.tonnage_mt || 10} MT capacity`,
                description: s.description || 'Critical raw materials storage facility registered in the European Data Space.',
                environmental_flags: s.environmental_flags || [],
                unfc_code: s.unfc_code || 'UNFC E1-F2-G1',
                color_theme: s.commodities && (s.commodities.includes('lithium') || s.commodities.includes('cobalt')) ? 'emerald' : 'gold'
              };
            });
          }
        }
      } catch (err) {
        console.warn('Backend fetch /api/sites omitted, using 100-site local dataset:', err);
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
            <div style="font-size: 11px; margin-bottom: 4px;"><strong>Commodities:</strong> ${site.commodities_label}</div>
            <div style="font-size: 10px; padding: 2px 6px; background: #e2e8f0; border-radius: 4px; display: inline-block;">${site.facility_type}</div>
            <button onclick="selectSite('${site.id}', true)" style="margin-top: 8px; width: 100%; padding: 4px; background: #047857; color: white; border: none; border-radius: 4px; font-size: 11px; font-weight: bold; cursor: pointer;">View Site Details</button>
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
          indicator.textContent = 'Gemini 1.5 Flash / Pro';
        } else if (provider === 'openai') {
          indicator.textContent = 'OpenAI GPT-4o';
        } else {
          indicator.textContent = 'Standalone Engine';
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
        query = "Show active lithium and cobalt waste dumps in Spain and Finland";
      } else if (scenarioId === 'query_2') {
        query = "Unrestored tungsten tailings ponds in Germany";
      } else if (scenarioId === 'query_3') {
        query = "Rare Earth Elements (REE) facilities in Sweden and France";
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
          <span class="animate-pulse font-mono text-emerald-400">Processing NLU Semantic Extraction & Solr Query...</span>
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
        
        let narrativeHtml = data.narrative || data.response_text || "Query processed successfully.";
        narrativeHtml = formatMarkdownText(narrativeHtml);

        let evidencesHtml = "";
        if (data.evidences && data.evidences.length > 0) {
          evidencesHtml = `<div class="mt-3 pt-3 border-t border-slate-800"><div class="text-[10px] text-amber-400 font-bold uppercase tracking-wider mb-2">📄 Technical PDF Evidence Snippets:</div>`;
          data.evidences.forEach(ev => {
            evidencesHtml += `
              <div class="bg-slate-950 p-2 rounded border border-slate-800/80 mb-2 text-[11px]">
                <div class="font-bold text-slate-200">${escapeHtml(ev.title)} (Page ${ev.page})</div>
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
            Server connection error: ${escapeHtml(err.message)}
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
        counter.textContent = `Showing ${matchedCount > 0 ? matchedCount : MINING_SITES.length} / ${MINING_SITES.length} European Sites`;
      }

      if (!container) return;
      container.innerHTML = '';

      if (!activeFilters || activeFilters.length === 0) {
        container.innerHTML = '<span class="text-slate-500 text-[10px] italic">No active filters (Showing full European Data Space)</span>';
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
    with open(path, "w", encoding="utf-8") as f:
        f.write(HTML_FULL_ENGLISH)
    print(f"Successfully wrote full English web application to: {path}")
