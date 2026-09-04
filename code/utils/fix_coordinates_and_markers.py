import json
import os
import random
import re

DATASET_PATH = r"C:\Users\fdemiguel\OneDrive - Universidad de Burgos\Documentos\CRMsDataSpace\SoftwareX\code\data\synthetic_escombreras_europe.json"
INDEX_PATHS = [
    r"C:\Users\fdemiguel\OneDrive - Universidad de Burgos\Documentos\CRMsDataSpace\SoftwareX\code\static\index.html",
    r"C:\Users\fdemiguel\OneDrive - Universidad de Burgos\Documentos\CRMsDataSpace\geo-rag-explorer\index.html"
]

with open(DATASET_PATH, "r", encoding="utf-8") as f:
    sites = json.load(f)

# Define accurate inland coordinate boundaries per region
REGIONAL_BOUNDS = {
    "spain": {
        "galicia": (42.2, 43.2, -8.3, -7.2),
        "castilla y leon": (41.2, 42.5, -6.0, -3.8),
        "extremadura": (38.8, 40.0, -6.5, -5.3),
        "andalucia": (37.3, 38.3, -5.2, -3.5),
        "asturias": (43.2, 43.5, -6.3, -5.3),
        "catalonia": (41.5, 42.2, 1.3, 2.5),
        "default": (40.0, 41.5, -4.5, -3.2)
    },
    "portugal": {
        "norte": (41.2, 41.9, -8.3, -7.3),
        "centro": (39.8, 40.7, -8.1, -7.2),
        "alentejo": (37.9, 39.0, -8.1, -7.4),
        "default": (39.5, 40.5, -8.0, -7.3)
    },
    "france": {
        "occitanie": (43.5, 44.4, 1.8, 3.6),
        "auvergne-rhone-alpes": (45.2, 46.1, 4.3, 6.0),
        "grand est": (48.3, 49.1, 5.6, 7.1),
        "nouvelle-aquitaine": (44.6, 45.8, -0.3, 1.1),
        "default": (46.0, 47.5, 2.0, 4.0)
    },
    "germany": {
        "saxony": (50.8, 51.3, 12.9, 14.1),
        "bavaria": (48.6, 49.9, 10.6, 12.4),
        "north rhine-westphalia": (50.9, 51.7, 6.9, 8.4),
        "default": (50.5, 52.0, 9.0, 11.5)
    },
    "sweden": {
        "norrbotten": (65.5, 67.2, 19.5, 21.8),
        "bergslagen": (59.8, 60.8, 14.6, 16.4),
        "vasterbotten": (64.1, 65.2, 18.6, 20.7),
        "default": (60.0, 63.0, 14.5, 17.5)
    },
    "finland": {
        "lapland": (66.3, 68.0, 25.1, 27.9),
        "north karelia": (62.3, 63.5, 28.6, 30.1),
        "kainuu": (64.1, 65.0, 27.6, 29.4),
        "default": (61.5, 64.0, 24.5, 28.0)
    },
    "poland": {
        "lower silesia": (50.8, 51.3, 15.9, 17.1),
        "upper silesia": (50.1, 50.6, 18.6, 19.7),
        "default": (51.0, 52.5, 17.0, 20.0)
    },
    "austria": {
        "styria": (47.0, 47.6, 14.3, 15.5),
        "carinthia": (46.6, 47.0, 13.6, 14.7),
        "default": (47.2, 48.2, 13.5, 15.5)
    },
    "italy": {
        "piedmont": (44.9, 45.8, 7.4, 8.4),
        "tuscany": (43.2, 43.9, 10.9, 11.7),
        "sardinia": (39.6, 40.4, 8.9, 9.4),
        "lombardy": (45.5, 46.1, 9.1, 10.1),
        "default": (42.5, 45.0, 10.5, 13.0)
    },
    "greece": {
        "central macedonia": (40.5, 41.1, 22.6, 23.7),
        "thrace": (41.0, 41.4, 24.9, 25.7),
        "default": (40.0, 41.2, 22.0, 24.0)
    },
    "ireland": {
        "leinster": (52.9, 53.5, -7.4, -6.6),
        "munster": (52.0, 52.6, -8.9, -8.1),
        "default": (52.5, 53.8, -8.0, -6.8)
    },
    "czechia": {
        "karlovy vary": (50.1, 50.4, 12.7, 13.1),
        "usti nad labem": (50.4, 50.8, 13.9, 14.4),
        "default": (49.5, 50.5, 13.5, 16.0)
    }
}

random.seed(42)

for s in sites:
    c = (s.get("country") or "spain").lower()
    reg = (s.get("region") or s.get("region_name") or "").lower()
    
    country_dict = REGIONAL_BOUNDS.get(c, REGIONAL_BOUNDS["spain"])
    bounds = country_dict.get(reg, country_dict.get("default"))
    
    min_lat, max_lat, min_lon, max_lon = bounds
    new_lat = round(random.uniform(min_lat, max_lat), 4)
    new_lon = round(random.uniform(min_lon, max_lon), 4)
    
    s["latitude"] = new_lat
    s["longitude"] = new_lon
    s["location"] = f"{new_lat},{new_lon}"

# Write back fixed coordinates to JSON dataset
with open(DATASET_PATH, "w", encoding="utf-8") as f:
    json.dump(sites, f, indent=2, ensure_ascii=False)

print(f"Updated 100 site coordinates in {DATASET_PATH}")

# Prepare JS dataset for HTML injection
js_sites = []
for s in sites:
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
        "lat": s["latitude"],
        "lon": s["longitude"],
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

# Update renderMarkers function in JS to draw LARGER, EASILY CLICKABLE CIRCLES
for path in INDEX_PATHS:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Re-inject MINING_SITES dataset
    content = re.sub(
        r'let MINING_SITES = \[[\s\S]*?\];',
        f'let MINING_SITES = {js_dataset_str};',
        content
    )

    # Enhance renderMarkers with LARGER circles and hover scale effects
    render_markers_pattern = r'function renderMarkers\(sitesToHighlight = null\) \{[\s\S]*?\}\n\n    function selectSite'
    
    new_render_markers = """function renderMarkers(sitesToHighlight = null) {
      if (!mapInstance) return;

      // Clear existing markers
      Object.values(markersMap).forEach(m => m.remove());
      markersMap = {};

      const highlightGroup = [];

      MINING_SITES.forEach(site => {
        const isMatched = !sitesToHighlight || sitesToHighlight.some(s => s.id === site.id);
        const opacity = isMatched ? 1.0 : 0.22;

        let color = '#10b981'; // Emerald
        let pulseClass = isMatched ? 'marker-pulse-emerald' : '';
        if (site.color_theme === 'gold') {
          color = '#fbbf24'; // Gold
          if (isMatched) pulseClass = 'marker-pulse-gold';
        }

        const isSelected = selectedSite && selectedSite.id === site.id;
        
        // LARGER CIRCLE SIZES FOR EASY CLICKING
        const size = isSelected ? 26 : (isMatched ? 20 : 12);
        const borderSize = isSelected ? 3 : 2;

        const customIcon = L.divIcon({
          className: 'custom-leaflet-marker',
          html: `<div class="${pulseClass} marker-circle-hover" style="
            width: ${size}px; 
            height: ${size}px; 
            background-color: ${color}; 
            border: ${borderSize}px solid #ffffff; 
            border-radius: 50%; 
            opacity: ${opacity};
            cursor: pointer;
            box-shadow: 0 0 16px ${color}aa;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
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
            <button onclick="selectSite('${site.id}', true)" style="margin-top: 8px; width: 100%; padding: 6px; background: #047857; color: white; border: none; border-radius: 6px; font-size: 11px; font-weight: bold; cursor: pointer;">View Site Details</button>
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
          mapInstance.fitBounds(bounds, { padding: [50, 50], maxZoom: 8 });
        } catch (e) {
          console.warn('Could not fit bounds:', e);
        }
      }
    }

    function selectSite"""

    content = re.sub(render_markers_pattern, new_render_markers, content)

    # Add hover CSS rule for marker circle zoom on mouseover
    if ".marker-circle-hover:hover" not in content:
      content = content.replace(
        ".marker-pulse-gold { animation: marker-pulse-gold 2s infinite; }",
        ".marker-pulse-gold { animation: marker-pulse-gold 2s infinite; }\n    .marker-circle-hover:hover { transform: scale(1.35); box-shadow: 0 0 24px #ffffff !important; z-index: 999; }"
      )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Successfully updated inland coordinates and enlarged markers in {path}")
