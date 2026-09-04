import os
import json
import math
import folium
import unicodedata
import gradio as gr
from pathlib import Path

# Add the directory to the path so we can import our custom modules
import sys
ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

from chat_agent import extract_filters, generate_natural_response
from mock_api import query_data_space, MOCK_DATABASE, load_database

# ----------------------------------------------------------------------
# UTM to Lat/Lon coordinate converter (Pure Python)
# ----------------------------------------------------------------------
def utm_to_latlon(easting: float, northing: float, zone: int = 30, northern_hemisphere: bool = True) -> tuple[float, float]:
    """
    Converts UTM coordinates (Zone 30N, WGS84 by default for Spain) to Latitude/Longitude.
    Accurate to within millimeters.
    """
    # WGS84 ellipsoid constants
    a = 6378137.0
    f = 1 / 298.257223563
    k0 = 0.9996
    
    b = a * (1 - f)
    e = math.sqrt(1 - (b/a)**2)
    e1sq = e**2 / (1 - e**2)
    
    x = easting - 500000.0
    y = northing
    if not northern_hemisphere:
        y -= 10000000.0
        
    lon0 = (zone * 6 - 183) * math.pi / 180.0
    
    # Footpoint latitude calculation
    n = (a - b) / (a + b)
    ap = a * (1.0 - n + (5.0/4.0)*(n**2 - n**3) + (81.0/64.0)*(n**4 - n**5))
    
    mu = y / (ap * (1.0 - e**2/4.0 - 3.0*e**4/64.0 - 5.0*e**6/256.0))
    e1 = (1.0 - math.sqrt(1.0 - e**2)) / (1.0 + math.sqrt(1.0 - e**2))
    j1 = (3.0*e1/2.0 - 27.0*e1**3/32.0)
    j2 = (21.0*e1**2/16.0 - 55.0*e1**4/32.0)
    j3 = (151.0*e1**3/96.0)
    j4 = (1097.0*e1**4/512.0)
    
    lat_fp = mu + j1*math.sin(2.0*mu) + j2*math.sin(4.0*mu) + j3*math.sin(6.0*mu) + j4*math.sin(8.0*mu)
    
    C1 = e1sq * math.cos(lat_fp)**2
    T1 = math.tan(lat_fp)**2
    N1 = a / math.sqrt(1.0 - (e*math.sin(lat_fp))**2)
    R1 = a * (1.0 - e**2) / (1.0 - (e*math.sin(lat_fp))**2)**1.5
    D = x / (N1 * k0)
    
    lat = lat_fp - (N1 * math.tan(lat_fp) / R1) * (
        D**2/2.0 - (5.0 + 3.0*T1 + 10.0*C1 - 4.0*C1**2 - 9.0*e1sq)*D**4/24.0 +
        (61.0 + 90.0*T1 + 298.0*C1 + 45.0*T1**2 - 252.0*e1sq - 3.0*C1**2)*D**6/720.0
    )
    
    lon = lon0 + (
        D - (1.0 + 2.0*T1 + C1)*D**3/6.0 +
        (5.0 - 2.0*C1 + 28.0*T1 - 3.0*C1**2 + 8.0*e1sq + 24.0*T1**2)*D**5/120.0
    ) / math.cos(lat_fp)
    
    return lat * 180.0 / math.pi, lon * 180.0 / math.pi


def get_site_coords(site: dict) -> tuple[float, float] | None:
    lat = site.get("lat")
    lon = site.get("lon")
    if lat is not None and lon is not None:
        return float(lat), float(lon)
    
    # Convert UTM coordinates if available
    utm_x = site.get("utm_x")
    utm_y = site.get("utm_y")
    utm_zone = site.get("utm_zone") or 30
    if utm_x is not None and utm_y is not None:
        try:
            return utm_to_latlon(float(utm_x), float(utm_y), zone=int(utm_zone))
        except Exception:
            pass
    return None


def clean_text(text: str) -> str:
    """Normalizes text by removing accents and converting to lowercase."""
    if not isinstance(text, str):
        return ""
    t = text.lower().strip()
    return "".join(
        c for c in unicodedata.normalize("NFD", t)
        if unicodedata.category(c) != "Mn"
    )

# ----------------------------------------------------------------------
# DB Filter Configuration and Dictionaries
# ----------------------------------------------------------------------
AVAILABLE_REGIONS = ["andalucia", "asturias", "castilla y leon", "galicia", "extremadura", "alentejo"]
AVAILABLE_COMMODITIES = ["coal", "copper", "silver", "gold", "tungsten", "tin", "lithium", "nickel", "cobalt", "zinc", "lead", "tantalum", "niobium"]
AVAILABLE_STATUSES = ["active", "inactive", "care and maintenance", "development"]

REGION_LABELS = {
    "andalucia": "Andalucía",
    "asturias": "Asturias",
    "castilla y leon": "Castilla y León",
    "galicia": "Galicia",
    "extremadura": "Extremadura",
    "alentejo": "Alentejo"
}

COMMODITY_LABELS = {
    "copper": "Cobre",
    "gold": "Oro",
    "silver": "Plata",
    "tungsten": "Wolframio",
    "tin": "Estaño",
    "lithium": "Litio",
    "nickel": "Níquel",
    "cobalt": "Cobalto",
    "zinc": "Zinc",
    "lead": "Plomo",
    "tantalum": "Tántalo",
    "niobium": "Niobio",
    "coal": "Carbón"
}

STATUS_LABELS = {
    "active": "Activo",
    "inactive": "Inactivo",
    "care and maintenance": "Mantenimiento",
    "development": "Desarrollo"
}

# ----------------------------------------------------------------------
# Simulated Detailed GIS Layer Data for each slag heap
# ----------------------------------------------------------------------
GIS_FEATURES = {
    "site_001": {  # Riotinto Project
        "samples": [
            {"id": "RT-S-01", "lat": 37.691, "lon": -6.588, "type": "Sondeo de Balsas", "depth": "15m", "grade": "0.45% Cu", "status": "Completado"},
            {"id": "RT-S-02", "lat": 37.689, "lon": -6.592, "type": "Trinchera de Relaves", "depth": "3m", "grade": "0.62% Cu", "status": "Completado"},
            {"id": "RT-S-03", "lat": 37.692, "lon": -6.591, "type": "Punto Geoquímico", "depth": "0.5m", "grade": "0.12% Cu", "status": "En progreso"},
            {"id": "RT-S-04", "lat": 37.688, "lon": -6.585, "type": "Sondeo Profundo", "depth": "25m", "grade": "0.58% Cu", "status": "Completado"}
        ],
        "grades": [
            {"id": "RT-G-High", "coords": [[37.688, -6.593], [37.690, -6.593], [37.690, -6.591], [37.688, -6.591]], "element": "copper", "grade": "Alto Grado (>0.5% Cu)", "color": "#d73027"},
            {"id": "RT-G-Medium", "coords": [[37.690, -6.591], [37.693, -6.591], [37.693, -6.587], [37.690, -6.587]], "element": "copper", "grade": "Medio Grado (0.2-0.5% Cu)", "color": "#fdae61"},
            {"id": "RT-G-Silver-High", "coords": [[37.689, -6.590], [37.691, -6.590], [37.691, -6.588], [37.689, -6.588]], "element": "silver", "grade": "Concentración Alta (>12 g/t Ag)", "color": "#74a9cf"},
            {"id": "RT-G-Gold-Low", "coords": [[37.691, -6.592], [37.693, -6.592], [37.693, -6.590], [37.691, -6.590]], "element": "gold", "grade": "Trazas de Oro (<0.1 g/t Au)", "color": "#ffd700"}
        ],
        "environmental": [
            {"id": "RT-E-Risk", "coords": [[37.686, -6.595], [37.692, -6.595], [37.692, -6.593], [37.686, -6.593]], "type": "Riesgo de Infiltración / Zona de Drenaje Crítica", "color": "#e6550d"}
        ]
    },
    "site_002": {  # El Valle-Boinás
        "samples": [
            {"id": "EV-S-01", "lat": 43.321, "lon": -6.318, "type": "Sondeo de Testigo", "depth": "50m", "grade": "2.1 g/t Au", "status": "Completado"},
            {"id": "EV-S-02", "lat": 43.319, "lon": -6.322, "type": "Trinchera Canal", "depth": "5m", "grade": "0.8 g/t Au", "status": "Completado"},
            {"id": "EV-S-03", "lat": 43.323, "lon": -6.320, "type": "Muestra Superficial", "depth": "0.1m", "grade": "0.3 g/t Au", "status": "En progreso"}
        ],
        "grades": [
            {"id": "EV-G-High", "coords": [[43.319, -6.323], [43.321, -6.323], [43.321, -6.321], [43.319, -6.321]], "element": "gold", "grade": "Alto Grado (>1.5 g/t Au)", "color": "#ffd700"},
            {"id": "EV-G-Medium", "coords": [[43.321, -6.321], [43.323, -6.321], [43.323, -6.318], [43.321, -6.318]], "element": "gold", "grade": "Bajo Grado (<1.5 g/t Au)", "color": "#fffacd"},
            {"id": "EV-G-Copper-Med", "coords": [[43.320, -6.320], [43.322, -6.320], [43.322, -6.319], [43.320, -6.319]], "element": "copper", "grade": "Mineralización de Cobre asociada (0.15% Cu)", "color": "#fdae61"}
        ],
        "environmental": [
            {"id": "EV-E-Restored", "coords": [[43.318, -6.324], [43.320, -6.324], [43.320, -6.322], [43.318, -6.322]], "type": "Zona Restaurada y Revegetada", "color": "#31a354"},
            {"id": "EV-E-Pending", "coords": [[43.322, -6.324], [43.324, -6.324], [43.324, -6.322], [43.322, -6.322]], "type": "Zona sin Restaurar (Estéril Expuesto)", "color": "#de2d26"}
        ]
    },
    "site_003": {  # Los Santos
        "samples": [
            {"id": "LS-S-01", "lat": 40.552, "lon": -5.788, "type": "Sondeo Rotación", "depth": "20m", "grade": "0.15% WO3", "status": "Completado"},
            {"id": "LS-S-02", "lat": 40.548, "lon": -5.792, "type": "Sondeo Rotación", "depth": "25m", "grade": "0.22% WO3", "status": "Completado"},
            {"id": "LS-S-03", "lat": 40.550, "lon": -5.790, "type": "Sondeo Planificado", "depth": "30m", "grade": "n/a", "status": "Planificado"}
        ],
        "grades": [
            {"id": "LS-G-High", "coords": [[40.549, -5.793], [40.551, -5.793], [40.551, -5.791], [40.549, -5.791]], "element": "tungsten", "grade": "Alta Concentración (>0.2% WO3)", "color": "#756bb1"},
            {"id": "LS-G-Low", "coords": [[40.551, -5.791], [40.553, -5.791], [40.553, -5.787], [40.551, -5.787]], "element": "tungsten", "grade": "Baja Concentración (0.05-0.2% WO3)", "color": "#bcbddc"}
        ],
        "environmental": [
            {"id": "LS-E-Reveg", "coords": [[40.547, -5.794], [40.550, -5.794], [40.550, -5.792], [40.547, -5.792]], "type": "Bermas revegetadas (en observación)", "color": "#a1d99b"}
        ]
    },
    "site_004": {  # San Finx
        "samples": [
            {"id": "SF-S-01", "lat": 42.751, "lon": -8.838, "type": "Muestra de Lodos", "depth": "2m", "grade": "0.35% Sn", "status": "Completado"},
            {"id": "SF-S-02", "lat": 42.749, "lon": -8.841, "type": "Sondeo Percusión", "depth": "10m", "grade": "0.10% WO3", "status": "Completado"}
        ],
        "grades": [
            {"id": "SF-G-Tin", "coords": [[42.748, -8.842], [42.752, -8.842], [42.752, -8.839], [42.748, -8.839]], "element": "tin", "grade": "Zona rica en Estaño (0.35% Sn)", "color": "#2c7fb8"},
            {"id": "SF-G-Tung", "coords": [[42.750, -8.841], [42.753, -8.841], [42.753, -8.837], [42.750, -8.837]], "element": "tungsten", "grade": "Zona rica en Wolframio (0.10% WO3)", "color": "#addd8e"}
        ],
        "environmental": [
            {"id": "SF-E-Acid", "coords": [[42.747, -8.844], [42.751, -8.844], [42.751, -8.841], [42.747, -8.841]], "type": "Potencial Drenaje Ácido de Mina", "color": "#e6550d"}
        ]
    },
    "site_005": {  # San José Valdeflórez
        "samples": [
            {"id": "SJV-S-01", "lat": 39.462, "lon": -6.358, "type": "Sondeo Diamantino", "depth": "120m", "grade": "0.98% Li2O", "status": "Completado"},
            {"id": "SJV-S-02", "lat": 39.458, "lon": -6.362, "type": "Sondeo Diamantino", "depth": "150m", "grade": "1.25% Li2O", "status": "Completado"},
            {"id": "SJV-S-03", "lat": 39.460, "lon": -6.360, "type": "Sondeo Planificado", "depth": "100m", "grade": "n/a", "status": "Planificado"}
        ],
        "grades": [
            {"id": "SJV-G-High", "coords": [[39.458, -6.363], [39.461, -6.363], [39.461, -6.360], [39.458, -6.360]], "element": "lithium", "grade": "Alto Grado (>1.0% Li2O)", "color": "#df65b0"},
            {"id": "SJV-G-Med", "coords": [[39.460, -6.360], [39.463, -6.360], [39.463, -6.357], [39.460, -6.357]], "element": "lithium", "grade": "Medio Grado (0.5-1.0% Li2O)", "color": "#e7298a"}
        ],
        "environmental": [
            {"id": "SJV-E-Buffer", "coords": [[39.456, -6.365], [39.464, -6.365], [39.464, -6.362], [39.456, -6.362]], "type": "Zona de Restricción Ambiental / Oposición Social", "color": "#756bb1"}
        ]
    }
}

# ----------------------------------------------------------------------
# Map Renderer with Location and GIS Layers
# ----------------------------------------------------------------------
def create_map(api_results: list, map_mode: str = "Marcadores de Ubicación", visible_layers: list = None, active_commodities: list = None, focus_coords: list = None, focus_zoom: int = 6) -> str:
    """
    Generates a folium map. Supports both site markers and dynamic GIS layering (polygons/points).
    """
    visible_layers = visible_layers or []
    active_commodities = active_commodities or []
    
    if focus_coords:
        m = folium.Map(location=focus_coords, zoom_start=focus_zoom, height="100%")
    else:
        m = folium.Map(location=[40.4168, -3.7038], zoom_start=6, height="100%")
        
    if map_mode == "Marcadores de Ubicación":
        for site in api_results:
            coords = get_site_coords(site)
            if coords:
                popup_html = f"<b>{site['site_name']}</b><br>"
                region_name = str(site.get('region') or '').title()
                popup_html += f"Región: {region_name}<br>"
                popup_html += f"Materiales: {', '.join(site.get('commodities', []))}<br>"
                status = site.get('project_status') or site.get('mine_status') or 'Desconocido'
                popup_html += f"Estado: {str(status).title()}"
                
                folium.Marker(
                    location=coords,
                    popup=folium.Popup(popup_html, max_width=300),
                    icon=folium.Icon(color="blue", icon="info-sign")
                ).add_to(m)
    else:
        # GIS Layers Mode
        samples_group = folium.FeatureGroup(name="Muestreos e Hitos (Sondeos)")
        grades_group = folium.FeatureGroup(name="Concentración (Grado del Elemento)")
        env_group = folium.FeatureGroup(name="Gestión Ambiental e Impacto")
        
        for site in api_results:
            coords = get_site_coords(site)
            if not coords:
                continue
                
            site_id = site.get("id")
            site_name = site.get("site_name")
            
            # Boundary limit for each site
            folium.Circle(
                location=coords,
                radius=350,
                color="darkblue",
                weight=1,
                fill=True,
                fill_color="blue",
                fill_opacity=0.03,
                popup=f"Concesión Minera: {site_name}"
            ).add_to(m)
            
            # Load simulated GIS features
            features = GIS_FEATURES.get(site_id)
            if not features:
                # Dynamically generate simulated GIS data for WARM sites so the map is never empty
                lat, lon = coords
                features = {
                    "samples": [
                        {"id": f"{site_id}-S-01", "lat": lat + 0.0006, "lon": lon + 0.0006, "type": "Sondeo de Control", "depth": "12m", "grade": "Estériles", "status": "Completado"},
                        {"id": f"{site_id}-S-02", "lat": lat - 0.0004, "lon": lon + 0.0008, "type": "Canal Geoquímico", "depth": "1m", "grade": "n/a", "status": "Planificado"}
                    ],
                    "grades": [
                        {"id": f"{site_id}-G-Main", "coords": [
                            [lat + 0.001, lon - 0.001],
                            [lat + 0.001, lon + 0.001],
                            [lat - 0.001, lon + 0.001],
                            [lat - 0.001, lon - 0.001]
                        ], "element": site.get("commodities", ["coal"])[0] if site.get("commodities") else "coal", "grade": "Zona de Acopio Principal", "color": "#74a9cf"}
                    ],
                    "environmental": [
                        {"id": f"{site_id}-E-Restor", "coords": [
                            [lat - 0.0015, lon - 0.0015],
                            [lat - 0.0008, lon - 0.0018],
                            [lat + 0.0005, lon - 0.0015],
                            [lat - 0.0008, lon + 0.0005]
                        ], "type": "Zona de Restauración Requerida", "color": "#feb24c"}
                    ]
                }
                
            # 1. Samples Layer
            if "samples" in visible_layers and "samples" in features:
                for s in features["samples"]:
                    desc = f"<b>Sondeo: {s['id']}</b><br>Tipo: {s['type']}<br>Profundidad: {s['depth']}<br>Estado: {s['status']}"
                    if s.get("grade") and s["grade"] != "n/a":
                        desc += f"<br>Ley/Grado: {s['grade']}"
                        
                    folium.CircleMarker(
                        location=[s["lat"], s["lon"]],
                        radius=6,
                        color="black",
                        weight=1,
                        fill=True,
                        fill_color="green" if s["status"] == "Completado" else "orange",
                        fill_opacity=0.8,
                        popup=folium.Popup(desc, max_width=250)
                    ).add_to(samples_group)
                    
            # 2. Grade/Concentration Layer
            if "grades" in visible_layers and "grades" in features:
                for g in features["grades"]:
                    if active_commodities and g.get("element") not in active_commodities:
                        continue
                    desc = f"<b>Capa de Mineralización ({g.get('element', '').upper()})</b><br>ID: {g['id']}<br>Fila/Clase: {g['grade']}"
                    folium.Polygon(
                        locations=g["coords"],
                        color="darkred",
                        weight=1,
                        fill=True,
                        fill_color=g["color"],
                        fill_opacity=0.5,
                        popup=folium.Popup(desc, max_width=250)
                    ).add_to(grades_group)
                    
            # 3. Environmental Layer
            if "environmental" in visible_layers and "environmental" in features:
                for e in features["environmental"]:
                    desc = f"<b>Capa Ambiental</b><br>Clase: {e['type']}"
                    folium.Polygon(
                        locations=e["coords"],
                        color="darkgreen" if "Restaurada" in e["type"] else "orange",
                        weight=1,
                        fill=True,
                        fill_color=e["color"],
                        fill_opacity=0.4,
                        popup=folium.Popup(desc, max_width=250)
                    ).add_to(env_group)
                    
        # Attach enabled groups
        if "samples" in visible_layers:
            samples_group.add_to(m)
        if "grades" in visible_layers:
            grades_group.add_to(m)
        if "environmental" in visible_layers:
            env_group.add_to(m)
            
        folium.LayerControl().add_to(m)
        
        # Inject HTML Legend Overlay directly inside Folium Map (Dark Theme styled)
        legend_html = '''
        <div style="
        position: fixed; 
        bottom: 20px; left: 20px; width: 280px; height: auto; 
        background-color: rgba(15, 23, 42, 0.95); border: 1px solid #334155; z-index: 9999; font-size: 12px;
        padding: 10px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        color: #cbd5e1;
        ">
        <details open>
            <summary style="font-weight: bold; color: #f8fafc; font-size: 13px; outline: none; cursor: pointer; user-select: none;">
                Leyenda GIS (Clic para ocultar)
            </summary>
            <hr style="margin: 5px 0; border: 0; border-top: 1px solid #334155;">
            <b>Concentración (Grado):</b><br>
            <div style="margin-top: 4px; margin-bottom: 4px; padding-left: 5px;">
                <i style="background:#d73027;width:12px;height:12px;float:left;margin-right:6px;opacity:0.7;border:1px solid #334155;display:inline-block;"></i> Alto Grado / Alta Densidad<br>
                <i style="background:#fdae61;width:12px;height:12px;float:left;margin-right:6px;opacity:0.7;border:1px solid #334155;display:inline-block;"></i> Medio Grado / Densidad Media<br>
                <i style="background:#ffd700;width:12px;height:12px;float:left;margin-right:6px;opacity:0.7;border:1px solid #334155;display:inline-block;"></i> Leyes de Oro (Au/Ag/Li/W)<br>
                <i style="background:#df65b0;width:12px;height:12px;float:left;margin-right:6px;opacity:0.7;border:1px solid #334155;display:inline-block;"></i> Leyes de Litio (Li2O)<br>
            </div>
            <hr style="margin: 5px 0; border: 0; border-top: 1px solid #334155;">
            <b>Muestreos y Sondeos:</b><br>
            <div style="margin-top: 4px; margin-bottom: 4px; padding-left: 5px;">
                <i style="background:green;border-radius:50%;width:10px;height:10px;float:left;margin-right:7px;border:1px solid #334155;display:inline-block;margin-top:2px;"></i> Muestra Completada (Borehole)<br>
                <i style="background:orange;border-radius:50%;width:10px;height:10px;float:left;margin-right:7px;border:1px solid #334155;display:inline-block;margin-top:2px;"></i> Muestra Planificada / En Progreso<br>
            </div>
            <hr style="margin: 5px 0; border: 0; border-top: 1px solid #334155;">
            <b>Gestión Ambiental:</b><br>
            <div style="margin-top: 4px; margin-bottom: 4px; padding-left: 5px;">
                <i style="background:#31a354;width:12px;height:12px;float:left;margin-right:6px;opacity:0.5;border:1px solid #334155;display:inline-block;"></i> Zona Restaurada y Revegetada<br>
                <i style="background:#e6550d;width:12px;height:12px;float:left;margin-right:6px;opacity:0.5;border:1px solid #334155;display:inline-block;"></i> Riesgo de Infiltración / Drenaje Ácido<br>
                <i style="background:#756bb1;width:12px;height:12px;float:left;margin-right:6px;opacity:0.5;border:1px solid #334155;display:inline-block;"></i> Buffer Ambiental / Exclusión Social<br>
            </div>
        </details>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
    return m._repr_html_()

# Initial map setup
initial_map_html = create_map(load_database())

# ----------------------------------------------------------------------
# CSS Styling for Premium Gradio UI
# ----------------------------------------------------------------------
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Apply Inter font globally */
body, html, .gradio-container, .gradio-container * {
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}

body {
    background-color: #0b0f19 !important; /* Deep dark blue-slate background */
    color: #cbd5e1 !important;
    margin: 0;
    padding: 0;
}

.gradio-container {
    max-width: 1600px !important;
    margin: 20px auto !important;
    border-radius: 16px;
    background: #0b0f19 !important; /* Unified dark background */
    padding: 10px 20px !important;
    box-shadow: none !important;
}

/* Page Header */
h1 {
    font-size: 1.75rem !important;
    color: #f8fafc !important;
    font-weight: 700 !important;
    letter-spacing: -0.025em;
    margin-bottom: 4px !important;
    background: none !important;
    -webkit-text-fill-color: initial !important;
}

/* Sidebar & columns boxes control */
.panel-border {
    border: none !important;
    border-radius: 0px !important;
    background: transparent !important;
    padding: 0px !important;
    box-shadow: none !important;
}

/* Section titles */
.sidebar-title h3, h3 {
    color: #f8fafc !important;
    font-weight: 600 !important;
    font-size: 1.05rem !important;
    margin-top: 0 !important;
    margin-bottom: 12px !important;
    border-bottom: none !important;
    padding-bottom: 0 !important;
    display: inline-block;
}

/* Dark, sleek cards for components */
.block {
    background: #0f172a !important; /* Slate 900 background */
    border: 1px solid #1e293b !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2), 0 2px 4px -1px rgba(0, 0, 0, 0.1) !important;
    padding: 12px !important;
    margin-bottom: 8px !important;
}

/* Form layouts and columns */
.form {
    padding: 0 !important;
    gap: 8px !important;
}

/* Custom buttons */
button.primary {
    background-color: #2563eb !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
button.primary:hover {
    background-color: #1d4ed8 !important;
    transform: translateY(-1px);
}

/* Accordion in Dark Mode */
.accordion {
    border: 1px solid #1e293b !important;
    background: #0f172a !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2) !important;
}

.accordion .label-wrap, .accordion button, .accordion .accordion-header {
    background-color: #1e293b !important; /* Dark header bg */
    color: #f8fafc !important; /* White-slate text */
    font-weight: 600 !important;
    border-bottom: 1px solid #334155 !important;
}

.accordion .label-wrap *, .accordion button *, .accordion .accordion-header * {
    color: #f8fafc !important; /* Force icons/labels to light grey/white */
}

.accordion .content, .accordion .accordion-content {
    background-color: #0f172a !important; /* slate-900 interior */
    padding: 12px !important;
}

/* Remove markdown default card boxes */
.prose, .markdown-text, .gradio-markdown {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

.prose p, .prose li, .prose h1, .prose h2, .prose h3, .prose h4 {
    color: #cbd5e1 !important;
}

/* Map container styling */
#map-view {
    padding: 0 !important;
    border-radius: 12px !important;
    border: 1px solid #1e293b !important;
    overflow: hidden;
    height: 70vh !important;
    margin-bottom: 0px !important;
    background-color: #0f172a !important;
}

#map-view div, #map-view iframe {
    width: 100% !important;
    height: 100% !important;
    border: none !important;
    display: block;
}

#chat-view {
    border-radius: 12px !important;
    border: 1px solid #1e293b !important;
    height: 70vh !important;
    background-color: #0f172a !important;
}

/* Adjust header labels of form components to be clean and professional */
.block-label, .block-title, [data-testid="block-info"] {
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: #94a3b8 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    margin-bottom: 6px !important;
    display: inline-block !important;
}

/* Inputs and interactive elements */
.gradio-container input, 
.gradio-container select, 
.gradio-container textarea,
.gradio-container .dropdown-container, 
.gradio-container .token {
    background-color: #1e293b !important; /* Dark input background */
    color: #f8fafc !important;
    border: 1px solid #334155 !important;
}

/* Radio/Checkbox Option Labels override - completely removes gray-on-blue/gray-on-gray */
.gradio-container label {
    background-color: #1e293b !important; /* Dark option unselected background */
    color: #cbd5e1 !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
}

.gradio-container label span {
    color: #cbd5e1 !important;
}

.gradio-container label:hover {
    background-color: #334155 !important;
}

.gradio-container label.selected {
    background-color: #2563eb !important; /* Vibrant blue when active */
    color: #ffffff !important; /* Pure white text */
    border-color: #3b82f6 !important;
}

.gradio-container label.selected span {
    color: #ffffff !important; /* Force white text when selected */
}

/* Dropdown list overrides */
.gradio-container .dropdown-menu, .gradio-container .dropdown-options {
    background-color: #1e293b !important;
    border: 1px solid #334155 !important;
    color: #f8fafc !important;
}

.gradio-container .dropdown-item, .gradio-container .option {
    color: #cbd5e1 !important;
}

.gradio-container .dropdown-item:hover, .gradio-container .option:hover {
    background-color: #334155 !important;
    color: #ffffff !important;
}

/* User vs Bot Chat Bubbles overrides to prevent white-on-gray or gray-on-gray readability issues */
.message-wrap .message.user, [data-testid="user-message"] {
    background-color: #2563eb !important; /* User bubble blue background */
    color: #ffffff !important; /* Pure white text */
    border: none !important;
}

.message-wrap .message.user *, [data-testid="user-message"] * {
    color: #ffffff !important;
}

.message-wrap .message.bot, [data-testid="bot-message"] {
    background-color: #1e293b !important; /* Bot bubble dark slate background */
    color: #f1f5f9 !important; /* Light text */
    border: 1px solid #334155 !important;
}

.message-wrap .message.bot *, [data-testid="bot-message"] * {
    color: #f1f5f9 !important;
}

/* Scrollbar styling */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background: #475569;
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: #64748b;
}

@media (max-width: 768px) {
    #map-view, #chat-view {
        height: 50vh !important;
        min-height: 300px;
    }
}

/* Group styling for integrated Chat block */
.gradio-container .group, .gradio-container div.group {
    background-color: #0f172a !important; /* slate-900 */
    border: 1px solid #1e293b !important;
    border-radius: 12px !important;
    padding: 0 !important;
    overflow: hidden;
    margin-bottom: 8px !important;
}

/* Ensure no double-borders inside the group */
.gradio-container .group #chat-view {
    border: none !important;
    border-bottom: 1px solid #1e293b !important;
    border-radius: 12px 12px 0 0 !important;
}

.gradio-container .group input, .gradio-container .group textarea {
    border: none !important;
    border-radius: 0 !important;
    background-color: #0f172a !important;
}

.gradio-container .group .row, .gradio-container .group div.row {
    padding: 8px !important;
    background-color: #0f172a !important;
    gap: 8px !important;
}

/* Gradio Dropdown overrides for absolute polish and visibility */
.gradio-container .dropdown-container {
    background-color: #1e293b !important;
    border: 1px solid #334155 !important;
    color: #f8fafc !important;
}

.gradio-container .dropdown-container input {
    background: transparent !important;
    border: none !important;
    color: #f8fafc !important;
}

.gradio-container .token-remove {
    color: #cbd5e1 !important;
}

/* Placeholder styling in dark mode */
.gradio-container input::placeholder, 
.gradio-container textarea::placeholder,
.gradio-container .placeholder {
    color: #64748b !important;
    opacity: 1 !important;
}
"""

# ----------------------------------------------------------------------
# Main Dashboard UI Build
# ----------------------------------------------------------------------
with gr.Blocks(title="CRMs Data Space GIS-Dashboard") as demo:
    
    gr.Markdown("# CRMs Data Space - Advanced GIS Dashboard")
    gr.Markdown("Visualizador avanzado de escombreras e integración de consultas en lenguaje natural con mapas por capas GIS.")
    
    with gr.Row():
        provider_dropdown = gr.Dropdown(
            choices=["Rules/WARM", "Local", "OpenAI", "Gemini"], 
            value="Rules/WARM", 
            label="Proveedor del LLM / Extractor"
        )
        
    with gr.Row():
        # LEFT COLUMN: Controls & Filters
        with gr.Column(scale=3, elem_classes=["panel-border"]):
            gr.Markdown("### Filtros y Capas GIS", elem_classes=["sidebar-title"])
            
            # Map Mode Selector
            map_mode_selector = gr.Radio(
                choices=["Marcadores de Ubicación", "GIS por Capas"],
                value="Marcadores de Ubicación",
                label="Modo de Visualización del Mapa"
            )
            
            # GIS Layer Checkboxes
            gis_layers = gr.CheckboxGroup(
                choices=[
                    ("Sondeos y Muestras", "samples"),
                    ("Concentración (Grado)", "grades"),
                    ("Gestión Ambiental/Riesgos", "environmental")
                ],
                value=["samples", "grades", "environmental"],
                label="Capas GIS Visibles (Modo GIS)",
                interactive=True
            )
            
            # Active Element Layer Dropdown
            active_comm_selector = gr.Dropdown(
                choices=[
                    ("Cobre", "copper"),
                    ("Oro", "gold"),
                    ("Plata", "silver"),
                    ("Wolframio", "tungsten"),
                    ("Estaño", "tin"),
                    ("Litio", "lithium"),
                    ("Níquel", "nickel"),
                    ("Cobalto", "cobalt"),
                    ("Zinc", "zinc"),
                    ("Plomo", "lead"),
                    ("Tántalo", "tantalum"),
                    ("Niobio", "niobium"),
                    ("Carbón", "coal")
                ],
                value=[],
                multiselect=True,
                label="Capa de Concentración del Elemento",
                info="Muestra sólo los elementos seleccionados. Si se deja vacío se muestran todos."
            )
            
            gr.HTML("<hr style='border: 0; border-top: 1px solid #e2e8f0; margin: 15px 0;'>")
            
            # DB Filter Checkboxes in a collapsible accordion to avoid occupying too much space
            with gr.Accordion("Filtros Avanzados", open=False):
                filter_region = gr.CheckboxGroup(
                    choices=[(REGION_LABELS.get(r, r.title()), r) for r in AVAILABLE_REGIONS],
                    label="Regiones detectadas",
                    interactive=True
                )
                filter_status = gr.CheckboxGroup(
                    choices=[(STATUS_LABELS.get(s, s.title()), s) for s in AVAILABLE_STATUSES],
                    label="Estado del proyecto",
                    interactive=True
                )
                filter_json = gr.Code(language="json", label="Filtros Crudos (JSON)", interactive=False)
            
        # CENTER COLUMN: Folium Map View
        with gr.Column(scale=5, elem_classes=["panel-border"]):
            gr.Markdown("### Visualizador Geospacial (IGME / WARM)", elem_classes=["sidebar-title"])
            map_view = gr.HTML(value=initial_map_html, elem_id="map-view")
            
        # RIGHT COLUMN: Assistant Chat
        with gr.Column(scale=4, elem_classes=["panel-border"]):
            gr.Markdown("### Asistente del Espacio de Datos", elem_classes=["sidebar-title"])
            with gr.Group():
                chatbot = gr.Chatbot(label="CRMs Assistant", height="58vh", elem_id="chat-view")
                msg = gr.Textbox(
                    placeholder="Escribe tu consulta (Ej: sondeos de cobre en Riotinto)...",
                    show_label=False
                )
                with gr.Row():
                    submit = gr.Button("Enviar", variant="primary")
                    clear = gr.ClearButton([msg, chatbot])
                
    # State Pipeline to pass values between steps
    state_pipeline = gr.State()

    def user_action(user_message, chat_history):
        if chat_history is None:
            chat_history = []
        chat_history.append({"role": "user", "content": str(user_message)})
        return "", chat_history

    def extract_and_update_filters(chat_history, provider_name, current_map_mode, current_gis_layers, current_active_comm):
        """
        Step 1: Extract filters from the user query, determine if GIS should be enabled,
        determine map focus, query the database, and render the map.
        """
        last_msg = chat_history[-1]
        
        # Extract text string
        if isinstance(last_msg, dict):
            user_message = last_msg.get("content", "")
        elif hasattr(last_msg, "content"):
            user_message = last_msg.content
        elif isinstance(last_msg, (list, tuple)):
            user_message = last_msg[0]
        else:
            user_message = str(last_msg)
            
        if isinstance(user_message, (list, tuple)):
            user_message = user_message[0] if len(user_message) > 0 else ""
            
        user_message_str = str(user_message)
        prov = "openai" if provider_name == "OpenAI" else ("gemini" if provider_name == "Gemini" else ("rules" if provider_name == "Rules/WARM" else "local"))
        
        # 1. Extract raw filters
        parsed_json = extract_filters(user_message_str, provider=prov)
        raw_filters = parsed_json.get("filters", {})
        

        # Dynamically add any extracted items to the choices to ensure we can select them
        current_regions = list(AVAILABLE_REGIONS)
        for r in raw_filters.get("regions", []):
            clean_r = clean_text(r)
            if clean_r and clean_r not in current_regions:
                current_regions.append(clean_r)
                
        current_commodities = list(AVAILABLE_COMMODITIES)
        for c in raw_filters.get("commodities", []):
            clean_c = clean_text(c)
            if clean_c and clean_c not in current_commodities:
                current_commodities.append(clean_c)

        reg_list = [clean_text(r) for r in raw_filters.get("regions", []) if clean_text(r) in current_regions]
        comm_list = [clean_text(c) for c in raw_filters.get("commodities", []) if clean_text(c) in current_commodities]
        stat_list = [clean_text(s) for s in raw_filters.get("project_status", []) if clean_text(s) in AVAILABLE_STATUSES]
        
        filters_dict = {}
        if reg_list: filters_dict["regions"] = reg_list
        if comm_list: filters_dict["commodities"] = comm_list
        if stat_list: filters_dict["project_status"] = stat_list
        
        # 2. Check query for GIS activation and parameters
        query_lower = clean_text(user_message_str)
        gis_keywords = ["gis", "capa", "capas", "muestreo", "sondeo", "muestra", "muestras", "ley", "leyes", "distribucion", "concentracion", "grado", "poligono"]
        
        map_mode = current_map_mode
        visible_layers = list(current_gis_layers)
        
        # Convert single string or list of elements into active_commodities list
        if isinstance(current_active_comm, str):
            active_commodities = [current_active_comm] if current_active_comm else []
        else:
            active_commodities = list(current_active_comm or [])
        
        # If user queries GIS/sampling keywords, auto-switch to GIS mode
        if any(kw in query_lower for kw in gis_keywords):
            map_mode = "GIS por Capas"
            
            # Auto-enable layers based on keywords
            if any(k in query_lower for k in ["muestreo", "sondeo", "muestra", "muestras"]):
                if "samples" not in visible_layers: visible_layers.append("samples")
            if any(k in query_lower for k in ["concentracion", "ley", "leyes", "grado", "distribucion"]):
                if "grades" not in visible_layers: visible_layers.append("grades")
            if any(k in query_lower for k in ["ambiental", "riesgo", "restauracion", "agua"]):
                if "environmental" not in visible_layers: visible_layers.append("environmental")
                
        # If user mentions specific commodities, auto-select them for concentration layer
        detected_commodities = raw_filters.get("commodities", [])
        if detected_commodities:
            for c in detected_commodities:
                clean_c = clean_text(c)
                if clean_c and clean_c not in active_commodities:
                    active_commodities.append(clean_c)
            if "grades" not in visible_layers:
                visible_layers.append("grades")
            map_mode = "GIS por Capas"
            
        # 3. Query Database
        api_results = query_data_space(filters_dict)
        
        # 4. Handle Zoom Map Focus on Specific Site or region
        focus_coords = None
        focus_zoom = 6
        
        # Check if a specific site is mentioned
        all_database = load_database()
        target_site = None
        for site in all_database:
            site_name_clean = clean_text(site.get("site_name", ""))
            aliases_clean = [clean_text(a) for a in site.get("aliases", [])]
            if site_name_clean in query_lower or any(a in query_lower for a in aliases_clean if len(a) > 3):
                target_site = site
                break
                
        if target_site:
            coords = get_site_coords(target_site)
            if coords:
                focus_coords = coords
                focus_zoom = 14  # Deep zoom for GIS analysis
        elif api_results:
            # If multiple results, center on the first one or average
            coords = get_site_coords(api_results[0])
            if coords:
                focus_coords = coords
                focus_zoom = 8 if len(api_results) > 1 else 14
                
        # 5. Render map HTML
        map_html = create_map(
            api_results=api_results, 
            map_mode=map_mode, 
            visible_layers=visible_layers, 
            active_commodities=active_commodities,
            focus_coords=focus_coords,
            focus_zoom=focus_zoom
        )
        
        # Save state
        json_str = json.dumps(filters_dict, indent=2, ensure_ascii=False)
        internal_state = {
            "query": user_message_str,
            "parsed_json": parsed_json,
            "api_results": api_results,
            "provider": prov,
            "focus_coords": focus_coords,
            "focus_zoom": focus_zoom
        }
        
        return (
            gr.CheckboxGroup(choices=[(REGION_LABELS.get(r, r.title()), r) for r in current_regions], value=reg_list),
            gr.CheckboxGroup(choices=[(STATUS_LABELS.get(s, s.title()), s) for s in AVAILABLE_STATUSES], value=stat_list),
            json_str,
            map_mode,
            visible_layers,
            gr.Dropdown(choices=[(COMMODITY_LABELS.get(c, c.title()), c) for c in current_commodities], value=active_commodities),
            map_html,
            internal_state
        )

    def generate_response_step(chat_history, internal_state):
        """
        Step 2: Generate natural language response
        """
        query = internal_state["query"]
        parsed_json = internal_state["parsed_json"]
        api_results = internal_state["api_results"]
        prov = internal_state["provider"]
        
        bot_response = generate_natural_response(query, parsed_json, api_results, provider=prov)
        
        # Add details if GIS is enabled and there are results
        if not api_results and prov == "rules":
            # Already returned appropriate empty message
            pass
        elif api_results and any(k in clean_text(query) for k in ["gis", "capa", "capas", "muestreo", "sondeo", "concentracion", "ley"]):
            bot_response += "\n\n**Nota del GIS**: He activado el mapa por capas para mostrarte la información geospacial solicitada (sondeos de control, áreas de concentración de mineral y zonas de restauración ambiental)."
            
        chat_history.append({"role": "assistant", "content": bot_response})
        return chat_history

    # Event handlers for submitting queries from chat
    action_1 = msg.submit(
        user_action, 
        [msg, chatbot], 
        [msg, chatbot], 
        queue=False
    )
    action_2 = action_1.then(
        extract_and_update_filters, 
        [chatbot, provider_dropdown, map_mode_selector, gis_layers, active_comm_selector], 
        [filter_region, filter_status, filter_json, map_mode_selector, gis_layers, active_comm_selector, map_view, state_pipeline]
    )
    action_2.then(
        generate_response_step,
        [chatbot, state_pipeline],
        [chatbot]
    )
    
    # Repeat for click button
    action_3 = submit.click(
        user_action, 
        [msg, chatbot], 
        [msg, chatbot], 
        queue=False
    )
    action_4 = action_3.then(
        extract_and_update_filters, 
        [chatbot, provider_dropdown, map_mode_selector, gis_layers, active_comm_selector], 
        [filter_region, filter_status, filter_json, map_mode_selector, gis_layers, active_comm_selector, map_view, state_pipeline]
    )
    action_4.then(
        generate_response_step,
        [chatbot, state_pipeline],
        [chatbot]
    )

    # Event handler for manual filter/layers change
    def manual_gis_update(map_mode, layers, active_commodities, regions, statuses, state):
        state = state or {}
        filters_dict = {}
        if regions: filters_dict["regions"] = regions
        if active_commodities: filters_dict["commodities"] = active_commodities
        if statuses: filters_dict["project_status"] = statuses
        
        api_results = query_data_space(filters_dict)
        
        # Keep previous zoom/center if available so it doesn't reset
        focus_coords = state.get("focus_coords")
        focus_zoom = state.get("focus_zoom", 6)
        
        old_results = state.get("api_results", [])
        old_ids = {s.get("id") for s in old_results}
        new_ids = {s.get("id") for s in api_results}
        
        if old_ids == new_ids and focus_coords:
            # Same results, keep zoom and center
            pass
        else:
            # Results changed, update zoom and center to show new results
            if api_results:
                coords = get_site_coords(api_results[0])
                if coords:
                    focus_coords = coords
                    focus_zoom = 8 if len(api_results) > 1 else 14
                    state["focus_coords"] = focus_coords
                    state["focus_zoom"] = focus_zoom
            else:
                focus_coords = None
                focus_zoom = 6
                state["focus_coords"] = None
                state["focus_zoom"] = 6
                
        # Save current results in state for next comparison
        state["api_results"] = api_results
                
        map_html = create_map(
            api_results=api_results, 
            map_mode=map_mode, 
            visible_layers=layers, 
            active_commodities=active_commodities,
            focus_coords=focus_coords,
            focus_zoom=focus_zoom
        )
        json_str = json.dumps(filters_dict, indent=2, ensure_ascii=False)
        return json_str, map_html, state

    # Wire up manual selectors
    manual_inputs = [map_mode_selector, gis_layers, active_comm_selector, filter_region, filter_status, state_pipeline]
    manual_outputs = [filter_json, map_view, state_pipeline]
    
    map_mode_selector.change(manual_gis_update, manual_inputs, manual_outputs)
    gis_layers.change(manual_gis_update, manual_inputs, manual_outputs)
    active_comm_selector.change(manual_gis_update, manual_inputs, manual_outputs)
    filter_region.change(manual_gis_update, manual_inputs, manual_outputs)
    filter_status.change(manual_gis_update, manual_inputs, manual_outputs)

if __name__ == "__main__":
    try:
        demo.launch(server_name="0.0.0.0", server_port=7865, share=False, theme=gr.themes.Soft(primary_hue="blue", secondary_hue="slate"), css=custom_css)
    except OSError:
        print("Port 7865 is busy (possibly in TIME_WAIT). Trying port 7866...")
        try:
            demo.launch(server_name="0.0.0.0", server_port=7866, share=False, theme=gr.themes.Soft(primary_hue="blue", secondary_hue="slate"), css=custom_css)
        except OSError:
            print("Port 7866 is busy. Launching on an automatically selected free port...")
            demo.launch(server_name="0.0.0.0", share=False, theme=gr.themes.Soft(primary_hue="blue", secondary_hue="slate"), css=custom_css)
