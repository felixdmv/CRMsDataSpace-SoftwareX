#!/usr/bin/env python3
"""
General-Purpose GIS Architecture Template Server:
Elsevier SoftwareX Demonstrator — Domain-Agnostic Conversational Spatial Search Sandbox.

Features:
- Zero external dependencies: Runs on standard Python 3.9+ (stdlib).
- Real-World World Map with Leaflet: Standard interactive world basemap with smooth regional navigation.
- 5 Areas of Interest (AOI):
    1. United States of America (with state-level resolution: California, Texas, Florida, NY, etc.)
    2. South America (Brazil, Argentina, Chile, Colombia, Peru, Ecuador, Bolivia, Uruguay, Paraguay)
    3. Europe (Spain, Germany, France, Italy, UK, Poland, Sweden, Netherlands, Portugal, Norway)
    4. Middle East (Saudi Arabia, UAE, Jordan, Qatar, Oman, Turkey)
    5. Southeast Asia & Oceania (Australia, New Zealand, Indonesia, Thailand, Vietnam, Philippines, Singapore, Malaysia)
- Country & State-Aware Spatial Generation: Points are generated with real GPS coordinates on land,
    automatically assigning the correct Country, State/Region, and realistic facility nomenclature.
- User-Driven Dynamic Schema & Filter Studio: Users can define custom filter dimensions or select presets.
- Decoupled 4-Stage Architecture Pipeline:
    Stage 1: Dynamic Conversational NLU & Token Extraction (including Country & State entities)
    Stage 2: Deterministic Schema Normalization & Validation
    Stage 3: Apache Solr-Style Boolean Query Builder ($q, fq$) & Live Multidimensional Facet Indexer
    Stage 4: Dynamic Cartographic Leaflet Synchronization
"""

import os
import sys
import json
import re
import random
import argparse
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from typing import Dict, Any, List, Optional, Tuple

TEMPLATE_DIR = Path(__file__).resolve().parent
DATA_FILE = TEMPLATE_DIR / "data" / "facilities.json"
CONFIG_FILE = TEMPLATE_DIR / "filters_config.json"
STATIC_DIR = TEMPLATE_DIR / "static"

# In-memory runtime state
_DATASET: List[Dict[str, Any]] = []
_CONFIG: Dict[str, Any] = {}

# ==============================================================================
# AREAS OF INTEREST (AOI) CATALOG & GEOGRAPHIC ANCHORS
# ==============================================================================

AREAS_OF_INTEREST: Dict[str, Dict[str, Any]] = {
    "usa": {
        "id": "usa",
        "name": "United States of America",
        "icon": "🇺🇸",
        "center": [39.8283, -98.5795],
        "zoom": 4.5,
        "bounds": [[24.5, -125.0], [49.5, -66.9]],
        "description": "Continental United States with state-level administrative resolution.",
        "subdivisions_type": "State",
        "subdivisions": {
            "California": {
                "name": "California", "code": "CA", "country": "United States",
                "center": [36.7783, -119.4179], "zoom": 6,
                "anchors": [
                    {"name": "Los Angeles Metro", "lat": 34.0522, "lon": -118.2437},
                    {"name": "San Francisco Bay Area", "lat": 37.7749, "lon": -122.4194},
                    {"name": "San Diego County", "lat": 32.7157, "lon": -117.1611},
                    {"name": "Central Valley / Fresno", "lat": 36.7468, "lon": -119.7726},
                    {"name": "Mojave Clean Energy Basin", "lat": 35.0110, "lon": -115.4734},
                    {"name": "Sacramento Valley", "lat": 38.5816, "lon": -121.4944}
                ]
            },
            "Texas": {
                "name": "Texas", "code": "TX", "country": "United States",
                "center": [31.9686, -99.9018], "zoom": 6,
                "anchors": [
                    {"name": "Houston Energy Corridor", "lat": 29.7604, "lon": -95.3698},
                    {"name": "Austin Tech & Grid Hub", "lat": 30.2672, "lon": -97.7431},
                    {"name": "Dallas-Fort Worth", "lat": 32.7767, "lon": -96.7970},
                    {"name": "Permian Infrastructure Basin", "lat": 31.8457, "lon": -102.3676},
                    {"name": "San Antonio District", "lat": 29.4241, "lon": -98.4936},
                    {"name": "West Texas Wind Corridor", "lat": 32.4487, "lon": -100.4085}
                ]
            },
            "Florida": {
                "name": "Florida", "code": "FL", "country": "United States",
                "center": [27.6648, -81.5158], "zoom": 6.5,
                "anchors": [
                    {"name": "Miami-Dade Coastal Area", "lat": 25.7617, "lon": -80.1918},
                    {"name": "Orlando Central Hub", "lat": 28.5383, "lon": -81.3792},
                    {"name": "Tampa Bay District", "lat": 27.9506, "lon": -82.4572},
                    {"name": "Jacksonville Logistics Port", "lat": 30.3322, "lon": -81.6557}
                ]
            },
            "New York": {
                "name": "New York", "code": "NY", "country": "United States",
                "center": [40.7128, -74.0060], "zoom": 6.5,
                "anchors": [
                    {"name": "New York Metro District", "lat": 40.7128, "lon": -74.0060},
                    {"name": "Albany Capital Region", "lat": 42.6526, "lon": -73.7562},
                    {"name": "Buffalo Niagara Region", "lat": 42.8864, "lon": -78.8784},
                    {"name": "Finger Lakes Area", "lat": 42.8864, "lon": -76.9930}
                ]
            },
            "Washington": {
                "name": "Washington", "code": "WA", "country": "United States",
                "center": [47.7511, -120.7401], "zoom": 6.5,
                "anchors": [
                    {"name": "Seattle Puget Sound", "lat": 47.6062, "lon": -122.3321},
                    {"name": "Columbia River Basin", "lat": 46.2304, "lon": -119.0921},
                    {"name": "Spokane Inland Empire", "lat": 47.6588, "lon": -117.4260}
                ]
            },
            "Illinois": {
                "name": "Illinois", "code": "IL", "country": "United States",
                "center": [40.6331, -89.3985], "zoom": 6.5,
                "anchors": [
                    {"name": "Chicago Metropolitan Area", "lat": 41.8781, "lon": -87.6298},
                    {"name": "Springfield Central Basin", "lat": 39.7817, "lon": -89.6501},
                    {"name": "Peoria Industrial Hub", "lat": 40.6936, "lon": -89.5890}
                ]
            },
            "Colorado": {
                "name": "Colorado", "code": "CO", "country": "United States",
                "center": [39.5501, -105.7821], "zoom": 6.5,
                "anchors": [
                    {"name": "Denver Front Range", "lat": 39.7392, "lon": -104.9903},
                    {"name": "Colorado Springs", "lat": 38.8339, "lon": -104.8214},
                    {"name": "Grand Junction Western Slope", "lat": 39.0639, "lon": -108.5506}
                ]
            },
            "Nevada": {
                "name": "Nevada", "code": "NV", "country": "United States",
                "center": [38.8026, -116.4194], "zoom": 6,
                "anchors": [
                    {"name": "Las Vegas Solar Basin", "lat": 36.1699, "lon": -115.1398},
                    {"name": "Reno-Tahoe Clean Tech Hub", "lat": 39.5296, "lon": -119.8138},
                    {"name": "Elko Mineral District", "lat": 40.8324, "lon": -115.7631}
                ]
            },
            "Arizona": {
                "name": "Arizona", "code": "AZ", "country": "United States",
                "center": [34.0489, -111.0937], "zoom": 6.5,
                "anchors": [
                    {"name": "Phoenix Sun Corridor", "lat": 33.4484, "lon": -112.0740},
                    {"name": "Tucson Desert Basin", "lat": 32.2226, "lon": -110.9747},
                    {"name": "Flagstaff Plateau", "lat": 35.1983, "lon": -111.6513}
                ]
            },
            "Pennsylvania": {
                "name": "Pennsylvania", "code": "PA", "country": "United States",
                "center": [41.2033, -77.1945], "zoom": 6.5,
                "anchors": [
                    {"name": "Philadelphia Industrial Area", "lat": 39.9526, "lon": -75.1652},
                    {"name": "Pittsburgh Energy Valley", "lat": 40.4406, "lon": -79.9959},
                    {"name": "Harrisburg Central Hub", "lat": 40.2732, "lon": -76.8867}
                ]
            }
        }
    },
    "south_america": {
        "id": "south_america",
        "name": "South America",
        "icon": "🌎",
        "center": [-15.0, -60.0],
        "zoom": 3.8,
        "bounds": [[-56.0, -82.0], [13.0, -34.0]],
        "description": "Entire South American continent across major federal republics.",
        "subdivisions_type": "Country",
        "subdivisions": {
            "Brazil": {
                "name": "Brazil", "code": "BR", "country": "Brazil",
                "center": [-14.2350, -51.9253], "zoom": 4.5,
                "anchors": [
                    {"name": "São Paulo Industrial Belt", "lat": -23.5505, "lon": -46.6333, "state": "São Paulo"},
                    {"name": "Rio de Janeiro Coastal Hub", "lat": -22.9068, "lon": -43.1729, "state": "Rio de Janeiro"},
                    {"name": "Belo Horizonte Mineral Corridor", "lat": -19.9167, "lon": -43.9345, "state": "Minas Gerais"},
                    {"name": "Salvador Northeastern Hub", "lat": -12.9777, "lon": -38.5016, "state": "Bahia"},
                    {"name": "Curitiba Clean Tech Basin", "lat": -25.4284, "lon": -49.2733, "state": "Paraná"},
                    {"name": "Brasília Federal District", "lat": -15.7975, "lon": -47.8919, "state": "Distrito Federal"},
                    {"name": "Porto Alegre Southern Hub", "lat": -30.0346, "lon": -51.2177, "state": "Rio Grande do Sul"}
                ]
            },
            "Argentina": {
                "name": "Argentina", "code": "AR", "country": "Argentina",
                "center": [-38.4161, -63.6167], "zoom": 4.5,
                "anchors": [
                    {"name": "Buenos Aires Metropolitan Area", "lat": -34.6037, "lon": -58.3816, "state": "Buenos Aires"},
                    {"name": "Córdoba Central Hub", "lat": -31.4201, "lon": -64.1888, "state": "Córdoba"},
                    {"name": "Mendoza Cuyo Valley", "lat": -32.8895, "lon": -68.8458, "state": "Mendoza"},
                    {"name": "Rosario Paraná Port", "lat": -32.9468, "lon": -60.6393, "state": "Santa Fe"},
                    {"name": "Neuquén Energy District", "lat": -38.9516, "lon": -68.0591, "state": "Neuquén"},
                    {"name": "Salta Northern Lithium Hub", "lat": -24.7821, "lon": -65.4232, "state": "Salta"}
                ]
            },
            "Chile": {
                "name": "Chile", "code": "CL", "country": "Chile",
                "center": [-35.6751, -71.5430], "zoom": 4.5,
                "anchors": [
                    {"name": "Santiago Central Valley", "lat": -33.4489, "lon": -70.6693, "state": "Santiago"},
                    {"name": "Antofagasta Atacama Mining District", "lat": -23.6509, "lon": -70.3975, "state": "Antofagasta"},
                    {"name": "Valparaíso Maritime Port", "lat": -33.0472, "lon": -71.6127, "state": "Valparaíso"},
                    {"name": "Concepción Industrial Zone", "lat": -36.8201, "lon": -73.0444, "state": "Biobío"},
                    {"name": "Calama Solar Corridor", "lat": -22.4544, "lon": -68.9294, "state": "Antofagasta"}
                ]
            },
            "Colombia": {
                "name": "Colombia", "code": "CO", "country": "Colombia",
                "center": [4.5709, -74.2973], "zoom": 5.5,
                "anchors": [
                    {"name": "Bogotá Sabana Region", "lat": 4.7110, "lon": -74.0721, "state": "Cundinamarca"},
                    {"name": "Medellín Tech & Energy Hub", "lat": 6.2442, "lon": -75.5812, "state": "Antioquia"},
                    {"name": "Cali Valle del Cauca", "lat": 3.4516, "lon": -76.5320, "state": "Valle del Cauca"},
                    {"name": "Barranquilla Caribbean Port", "lat": 10.9685, "lon": -74.7813, "state": "Atlántico"}
                ]
            },
            "Peru": {
                "name": "Peru", "code": "PE", "country": "Peru",
                "center": [-9.1900, -75.0152], "zoom": 5,
                "anchors": [
                    {"name": "Lima Coastal Industrial Hub", "lat": -12.0464, "lon": -77.0428, "state": "Lima"},
                    {"name": "Arequipa Southern Hub", "lat": -16.4090, "lon": -71.5375, "state": "Arequipa"},
                    {"name": "Cusco Highlands", "lat": -13.5319, "lon": -71.9675, "state": "Cusco"},
                    {"name": "Trujillo Northern Port", "lat": -8.1116, "lon": -79.0287, "state": "La Libertad"}
                ]
            },
            "Ecuador": {
                "name": "Ecuador", "code": "EC", "country": "Ecuador",
                "center": [-1.8312, -78.1834], "zoom": 6.5,
                "anchors": [
                    {"name": "Quito Andean Corridor", "lat": -0.1807, "lon": -78.4678, "state": "Pichincha"},
                    {"name": "Guayaquil Port District", "lat": -2.1894, "lon": -79.8891, "state": "Guayas"},
                    {"name": "Cuenca Southern Basin", "lat": -2.9001, "lon": -79.0059, "state": "Azuay"}
                ]
            },
            "Bolivia": {
                "name": "Bolivia", "code": "BO", "country": "Bolivia",
                "center": [-16.2902, -63.5887], "zoom": 5.5,
                "anchors": [
                    {"name": "Santa Cruz Industrial Hub", "lat": -17.7863, "lon": -63.1812, "state": "Santa Cruz"},
                    {"name": "La Paz Altiplano", "lat": -16.5000, "lon": -68.1500, "state": "La Paz"},
                    {"name": "Potosí Uyuni Salar Basin", "lat": -19.5836, "lon": -65.7531, "state": "Potosí"}
                ]
            },
            "Uruguay": {
                "name": "Uruguay", "code": "UY", "country": "Uruguay",
                "center": [-32.5228, -55.7658], "zoom": 7,
                "anchors": [
                    {"name": "Montevideo Clean Energy Hub", "lat": -34.9011, "lon": -56.1645, "state": "Montevideo"},
                    {"name": "Salto Solar & Hydro Corridor", "lat": -31.3833, "lon": -57.9667, "state": "Salto"}
                ]
            },
            "Paraguay": {
                "name": "Paraguay", "code": "PY", "country": "Paraguay",
                "center": [-23.4425, -58.4438], "zoom": 6.5,
                "anchors": [
                    {"name": "Asunción Capital Corridor", "lat": -25.2637, "lon": -57.5759, "state": "Central"},
                    {"name": "Ciudad del Este Itaipú Dam Hub", "lat": -25.5097, "lon": -54.6111, "state": "Alto Paraná"}
                ]
            }
        }
    },
    "europe": {
        "id": "europe",
        "name": "Europe",
        "icon": "🇪🇺",
        "center": [50.0, 10.0],
        "zoom": 4.2,
        "bounds": [[35.0, -11.0], [70.0, 32.0]],
        "description": "Entire European region across Western, Central, Southern, and Nordic countries.",
        "subdivisions_type": "Country",
        "subdivisions": {
            "Spain": {
                "name": "Spain", "code": "ES", "country": "Spain",
                "center": [40.4637, -3.7492], "zoom": 6,
                "anchors": [
                    {"name": "Madrid Central Hub", "lat": 40.4168, "lon": -3.7038, "state": "Madrid"},
                    {"name": "Barcelona Mediterranean Hub", "lat": 41.3851, "lon": 2.1734, "state": "Cataluña"},
                    {"name": "Sevilla Solar Valley", "lat": 37.3891, "lon": -5.9845, "state": "Andalucía"},
                    {"name": "Bilbao Industrial Corridor", "lat": 43.2630, "lon": -2.9350, "state": "País Vasco"},
                    {"name": "Valencia Energy Basin", "lat": 39.4699, "lon": -0.3763, "state": "Valencia"}
                ]
            },
            "Germany": {
                "name": "Germany", "code": "DE", "country": "Germany",
                "center": [51.1657, 10.4515], "zoom": 6,
                "anchors": [
                    {"name": "Berlin Capital Tech Hub", "lat": 52.5200, "lon": 13.4050, "state": "Berlin"},
                    {"name": "Munich Bavarian Tech Cluster", "lat": 48.1351, "lon": 11.5820, "state": "Bavaria"},
                    {"name": "Frankfurt Financial & Grid Core", "lat": 50.1109, "lon": 8.6821, "state": "Hesse"},
                    {"name": "Hamburg Maritime Wind Port", "lat": 53.5511, "lon": 9.9937, "state": "Hamburg"},
                    {"name": "Stuttgart Industrial Basin", "lat": 48.7758, "lon": 9.1829, "state": "Baden-Württemberg"},
                    {"name": "Cologne Rhine-Ruhr Corridor", "lat": 50.9375, "lon": 6.9603, "state": "North Rhine-Westphalia"}
                ]
            },
            "France": {
                "name": "France", "code": "FR", "country": "France",
                "center": [46.2276, 2.2137], "zoom": 6,
                "anchors": [
                    {"name": "Paris Île-de-France Hub", "lat": 48.8566, "lon": 2.3522, "state": "Île-de-France"},
                    {"name": "Lyon Rhône-Alpes Energy Basin", "lat": 45.7640, "lon": 4.8357, "state": "Auvergne-Rhône-Alpes"},
                    {"name": "Marseille Mediterranean Port", "lat": 43.2965, "lon": 5.3698, "state": "Provence-Alpes-Côte d'Azur"},
                    {"name": "Toulouse Aerospace & Tech Valley", "lat": 43.6047, "lon": 1.4442, "state": "Occitanie"},
                    {"name": "Bordeaux Atlantic Hub", "lat": 44.8378, "lon": -0.5792, "state": "Nouvelle-Aquitaine"}
                ]
            },
            "Italy": {
                "name": "Italy", "code": "IT", "country": "Italy",
                "center": [41.8719, 12.5674], "zoom": 6,
                "anchors": [
                    {"name": "Rome Capital Basin", "lat": 41.9028, "lon": 12.4964, "state": "Lazio"},
                    {"name": "Milan Lombardy Tech Core", "lat": 45.4642, "lon": 9.1900, "state": "Lombardy"},
                    {"name": "Turin Industrial Valley", "lat": 45.0703, "lon": 7.6869, "state": "Piedmont"},
                    {"name": "Naples Southern District", "lat": 40.8518, "lon": 14.2681, "state": "Campania"}
                ]
            },
            "United Kingdom": {
                "name": "United Kingdom", "code": "GB", "country": "United Kingdom",
                "center": [55.3781, -3.4360], "zoom": 6,
                "anchors": [
                    {"name": "London Thames Hub", "lat": 51.5074, "lon": -0.1278, "state": "England"},
                    {"name": "Manchester Northern Powerhouse", "lat": 53.4808, "lon": -2.2426, "state": "England"},
                    {"name": "Edinburgh Scottish Clean Tech Hub", "lat": 55.9533, "lon": -3.1883, "state": "Scotland"},
                    {"name": "Cardiff Welsh Coastal Port", "lat": 51.4816, "lon": -3.1791, "state": "Wales"}
                ]
            },
            "Poland": {
                "name": "Poland", "code": "PL", "country": "Poland",
                "center": [51.9194, 19.1451], "zoom": 6,
                "anchors": [
                    {"name": "Warsaw Mazovia Core", "lat": 52.2297, "lon": 21.0122, "state": "Mazovia"},
                    {"name": "Kraków Southern Tech Hub", "lat": 50.0647, "lon": 19.9450, "state": "Lesser Poland"},
                    {"name": "Wrocław Silesia Innovation Hub", "lat": 51.1079, "lon": 17.0385, "state": "Lower Silesia"}
                ]
            },
            "Sweden": {
                "name": "Sweden", "code": "SE", "country": "Sweden",
                "center": [60.1282, 18.6435], "zoom": 5,
                "anchors": [
                    {"name": "Stockholm Capital Tech Hub", "lat": 59.3293, "lon": 18.0686, "state": "Stockholm"},
                    {"name": "Gothenburg Maritime Hub", "lat": 57.7089, "lon": 11.9746, "state": "Västra Götaland"},
                    {"name": "Malmö Skåne Clean Tech Area", "lat": 55.6050, "lon": 13.0038, "state": "Skåne"}
                ]
            },
            "Netherlands": {
                "name": "Netherlands", "code": "NL", "country": "Netherlands",
                "center": [52.1326, 5.2913], "zoom": 7,
                "anchors": [
                    {"name": "Amsterdam Tech Core", "lat": 52.3676, "lon": 4.9041, "state": "North Holland"},
                    {"name": "Rotterdam Energy Port", "lat": 51.9244, "lon": 4.4777, "state": "South Holland"},
                    {"name": "Eindhoven High-Tech Campus", "lat": 51.4416, "lon": 5.4697, "state": "North Brabant"}
                ]
            }
        }
    },
    "middle_east": {
        "id": "middle_east",
        "name": "Middle East",
        "icon": "🏜️",
        "center": [26.0, 47.0],
        "zoom": 4.5,
        "bounds": [[12.0, 32.0], [42.0, 62.0]],
        "description": "Arabian Peninsula and Levant regions.",
        "subdivisions_type": "Country",
        "subdivisions": {
            "Saudi Arabia": {
                "name": "Saudi Arabia", "code": "SA", "country": "Saudi Arabia",
                "center": [23.8859, 45.0792], "zoom": 5,
                "anchors": [
                    {"name": "Riyadh Central Plateau", "lat": 24.7136, "lon": 46.6753, "state": "Riyadh"},
                    {"name": "Jeddah Red Sea Coastal Hub", "lat": 21.4858, "lon": 39.1925, "state": "Makkah"},
                    {"name": "Dammam Eastern Energy Basin", "lat": 26.4207, "lon": 50.0888, "state": "Eastern Province"},
                    {"name": "NEOM Clean Tech Region", "lat": 28.0000, "lon": 35.2000, "state": "Tabuk"}
                ]
            },
            "United Arab Emirates": {
                "name": "United Arab Emirates", "code": "AE", "country": "United Arab Emirates",
                "center": [23.4241, 53.8478], "zoom": 7,
                "anchors": [
                    {"name": "Abu Dhabi Masdar Clean City", "lat": 24.4539, "lon": 54.3773, "state": "Abu Dhabi"},
                    {"name": "Dubai Innovation & Solar Corridor", "lat": 25.2048, "lon": 55.2708, "state": "Dubai"},
                    {"name": "Sharjah Industrial Hub", "lat": 25.3463, "lon": 55.4209, "state": "Sharjah"}
                ]
            },
            "Jordan": {
                "name": "Jordan", "code": "JO", "country": "Jordan",
                "center": [30.5852, 36.2384], "zoom": 7,
                "anchors": [
                    {"name": "Amman Capital District", "lat": 31.9454, "lon": 35.9284, "state": "Amman"},
                    {"name": "Aqaba Red Sea Solar Port", "lat": 29.5320, "lon": 35.0063, "state": "Aqaba"},
                    {"name": "Irbid Northern Valley", "lat": 32.5568, "lon": 35.8469, "state": "Irbid"}
                ]
            },
            "Qatar": {
                "name": "Qatar", "code": "QA", "country": "Qatar",
                "center": [25.3548, 51.1839], "zoom": 8,
                "anchors": [
                    {"name": "Doha Central Hub", "lat": 25.2854, "lon": 51.5310, "state": "Doha"},
                    {"name": "Ras Laffan Industrial Core", "lat": 25.9000, "lon": 51.5300, "state": "Al Khor"}
                ]
            },
            "Oman": {
                "name": "Oman", "code": "OM", "country": "Oman",
                "center": [21.4735, 55.9754], "zoom": 6,
                "anchors": [
                    {"name": "Muscat Coastal District", "lat": 23.5880, "lon": 58.3829, "state": "Muscat"},
                    {"name": "Salalah Southern Wind Corridor", "lat": 17.0151, "lon": 54.0924, "state": "Dhofar"},
                    {"name": "Sohar Industrial Port", "lat": 24.3461, "lon": 56.7075, "state": "Al Batinah North"}
                ]
            },
            "Turkey": {
                "name": "Turkey", "code": "TR", "country": "Turkey",
                "center": [38.9637, 35.2433], "zoom": 5.5,
                "anchors": [
                    {"name": "Istanbul Bosporus Hub", "lat": 41.0082, "lon": 28.9784, "state": "Marmara"},
                    {"name": "Ankara Central Anatolia", "lat": 39.9334, "lon": 32.8597, "state": "Central Anatolia"},
                    {"name": "Izmir Aegean Solar Corridor", "lat": 38.4237, "lon": 27.1428, "state": "Aegean"}
                ]
            }
        }
    },
    "southeast_asia_oceania": {
        "id": "southeast_asia_oceania",
        "name": "Southeast Asia & Oceania",
        "icon": "🌏",
        "center": [-5.0, 125.0],
        "zoom": 3.8,
        "bounds": [[-47.0, 95.0], [25.0, 180.0]],
        "description": "Australia, New Zealand, Indonesia, Thailand, Vietnam, Philippines, Singapore, Malaysia.",
        "subdivisions_type": "Country",
        "subdivisions": {
            "Australia": {
                "name": "Australia", "code": "AU", "country": "Australia",
                "center": [-25.2744, 133.7751], "zoom": 4.5,
                "anchors": [
                    {"name": "Sydney Solar & Grid Hub", "lat": -33.8688, "lon": 151.2093, "state": "New South Wales"},
                    {"name": "Melbourne Tech Basin", "lat": -37.8136, "lon": 144.9631, "state": "Victoria"},
                    {"name": "Brisbane Sunshine Energy Corridor", "lat": -27.4698, "lon": 153.0251, "state": "Queensland"},
                    {"name": "Perth Clean Tech & Lithium Basin", "lat": -31.9505, "lon": 115.8605, "state": "Western Australia"},
                    {"name": "Adelaide Renewable Grid Hub", "lat": -34.9285, "lon": 138.6007, "state": "South Australia"},
                    {"name": "Pilbara Renewable Superhub", "lat": -21.1783, "lon": 119.7460, "state": "Western Australia"},
                    {"name": "Hobart Hydro Basin", "lat": -42.8821, "lon": 147.3272, "state": "Tasmania"}
                ]
            },
            "New Zealand": {
                "name": "New Zealand", "code": "NZ", "country": "New Zealand",
                "center": [-40.9006, 174.8860], "zoom": 5.5,
                "anchors": [
                    {"name": "Auckland Tech Hub", "lat": -36.8485, "lon": 174.7633, "state": "Auckland"},
                    {"name": "Wellington Wind & Marine Port", "lat": -41.2865, "lon": 174.7762, "state": "Wellington"},
                    {"name": "Christchurch Geothermal & Grid Hub", "lat": -43.5321, "lon": 172.6362, "state": "Canterbury"},
                    {"name": "Otago Hydro Region", "lat": -45.0312, "lon": 168.6626, "state": "Otago"}
                ]
            },
            "Indonesia": {
                "name": "Indonesia", "code": "ID", "country": "Indonesia",
                "center": [-0.7893, 113.9213], "zoom": 5,
                "anchors": [
                    {"name": "Jakarta Java Central Hub", "lat": -6.2088, "lon": 106.8456, "state": "Java"},
                    {"name": "Surabaya Eastern Industrial Zone", "lat": -7.2575, "lon": 112.7521, "state": "East Java"},
                    {"name": "Bandung Tech Valley", "lat": -6.9175, "lon": 107.6191, "state": "West Java"},
                    {"name": "Medan Sumatra Corridor", "lat": 3.5952, "lon": 98.6722, "state": "North Sumatra"},
                    {"name": "Bali Green Energy Zone", "lat": -8.4095, "lon": 115.1889, "state": "Bali"}
                ]
            },
            "Thailand": {
                "name": "Thailand", "code": "TH", "country": "Thailand",
                "center": [15.8700, 100.9925], "zoom": 5.5,
                "anchors": [
                    {"name": "Bangkok Eastern Economic Corridor", "lat": 13.7563, "lon": 100.5018, "state": "Bangkok"},
                    {"name": "Chiang Mai Northern Clean Tech", "lat": 18.7883, "lon": 98.9853, "state": "Chiang Mai"},
                    {"name": "Chonburi Solar Valley", "lat": 13.3611, "lon": 100.9847, "state": "Chonburi"}
                ]
            },
            "Vietnam": {
                "name": "Vietnam", "code": "VN", "country": "Vietnam",
                "center": [14.0583, 108.2772], "zoom": 5.5,
                "anchors": [
                    {"name": "Hanoi Red River Basin", "lat": 21.0285, "lon": 105.8542, "state": "Hanoi"},
                    {"name": "Ho Chi Minh City Innovation Hub", "lat": 10.8231, "lon": 106.6297, "state": "Ho Chi Minh"},
                    {"name": "Da Nang Coastal Tech Hub", "lat": 16.0544, "lon": 108.2022, "state": "Da Nang"},
                    {"name": "Ninh Thuan Wind & Solar Capital", "lat": 11.5645, "lon": 108.9950, "state": "Ninh Thuan"}
                ]
            },
            "Philippines": {
                "name": "Philippines", "code": "PH", "country": "Philippines",
                "center": [12.8797, 121.7740], "zoom": 5.5,
                "anchors": [
                    {"name": "Metro Manila Urban Grid", "lat": 14.5995, "lon": 120.9842, "state": "NCR"},
                    {"name": "Cebu Visayas Maritime Hub", "lat": 10.3157, "lon": 123.8854, "state": "Cebu"},
                    {"name": "Davao Southern Clean Energy Hub", "lat": 7.1907, "lon": 125.4553, "state": "Davao"}
                ]
            },
            "Singapore": {
                "name": "Singapore", "code": "SG", "country": "Singapore",
                "center": [1.3521, 103.8198], "zoom": 11,
                "anchors": [
                    {"name": "Jurong CleanTech Park", "lat": 1.3483, "lon": 103.6831, "state": "Jurong"},
                    {"name": "Marina Bay Floating Solar District", "lat": 1.2838, "lon": 103.8591, "state": "Central"},
                    {"name": "Changi Airport Energy Grid", "lat": 1.3644, "lon": 103.9915, "state": "East"}
                ]
            },
            "Malaysia": {
                "name": "Malaysia", "code": "MY", "country": "Malaysia",
                "center": [4.2105, 101.9758], "zoom": 6,
                "anchors": [
                    {"name": "Kuala Lumpur Klang Valley", "lat": 3.1390, "lon": 101.6869, "state": "Selangor"},
                    {"name": "Penang Silicon Island Hub", "lat": 5.4141, "lon": 100.3288, "state": "Penang"},
                    {"name": "Johor Southern Tech Corridor", "lat": 1.4927, "lon": 103.7414, "state": "Johor"}
                ]
            }
        }
    }
}

# Synonyms and aliases for countries, states, and geographic keywords
GEOGRAPHIC_ALIASES: Dict[str, Dict[str, str]] = {
    # Countries
    "australia": {"type": "country", "canonical": "Australia"},
    "nueva zelanda": {"type": "country", "canonical": "New Zealand"},
    "new zealand": {"type": "country", "canonical": "New Zealand"},
    "indonesia": {"type": "country", "canonical": "Indonesia"},
    "tailandia": {"type": "country", "canonical": "Thailand"},
    "thailand": {"type": "country", "canonical": "Thailand"},
    "vietnam": {"type": "country", "canonical": "Vietnam"},
    "filipinas": {"type": "country", "canonical": "Philippines"},
    "philippines": {"type": "country", "canonical": "Philippines"},
    "singapur": {"type": "country", "canonical": "Singapore"},
    "singapore": {"type": "country", "canonical": "Singapore"},
    "malasia": {"type": "country", "canonical": "Malaysia"},
    "malaysia": {"type": "country", "canonical": "Malaysia"},
    "estados unidos": {"type": "country", "canonical": "United States"},
    "eeuu": {"type": "country", "canonical": "United States"},
    "ee.uu.": {"type": "country", "canonical": "United States"},
    "usa": {"type": "country", "canonical": "United States"},
    "us": {"type": "country", "canonical": "United States"},
    "united states": {"type": "country", "canonical": "United States"},
    "brasil": {"type": "country", "canonical": "Brazil"},
    "brazil": {"type": "country", "canonical": "Brazil"},
    "argentina": {"type": "country", "canonical": "Argentina"},
    "chile": {"type": "country", "canonical": "Chile"},
    "colombia": {"type": "country", "canonical": "Colombia"},
    "peru": {"type": "country", "canonical": "Peru"},
    "perú": {"type": "country", "canonical": "Peru"},
    "ecuador": {"type": "country", "canonical": "Ecuador"},
    "bolivia": {"type": "country", "canonical": "Bolivia"},
    "uruguay": {"type": "country", "canonical": "Uruguay"},
    "paraguay": {"type": "country", "canonical": "Paraguay"},
    "espana": {"type": "country", "canonical": "Spain"},
    "españa": {"type": "country", "canonical": "Spain"},
    "spain": {"type": "country", "canonical": "Spain"},
    "alemania": {"type": "country", "canonical": "Germany"},
    "germany": {"type": "country", "canonical": "Germany"},
    "deutschland": {"type": "country", "canonical": "Germany"},
    "francia": {"type": "country", "canonical": "France"},
    "france": {"type": "country", "canonical": "France"},
    "italia": {"type": "country", "canonical": "Italy"},
    "italy": {"type": "country", "canonical": "Italy"},
    "reino unido": {"type": "country", "canonical": "United Kingdom"},
    "uk": {"type": "country", "canonical": "United Kingdom"},
    "united kingdom": {"type": "country", "canonical": "United Kingdom"},
    "polonia": {"type": "country", "canonical": "Poland"},
    "poland": {"type": "country", "canonical": "Poland"},
    "suecia": {"type": "country", "canonical": "Sweden"},
    "sweden": {"type": "country", "canonical": "Sweden"},
    "paises bajos": {"type": "country", "canonical": "Netherlands"},
    "holanda": {"type": "country", "canonical": "Netherlands"},
    "netherlands": {"type": "country", "canonical": "Netherlands"},
    "portugal": {"type": "country", "canonical": "Portugal"},
    "noruega": {"type": "country", "canonical": "Norway"},
    "arabia saudi": {"type": "country", "canonical": "Saudi Arabia"},
    "arabia saudita": {"type": "country", "canonical": "Saudi Arabia"},
    "saudi arabia": {"type": "country", "canonical": "Saudi Arabia"},
    "emiratos arabes": {"type": "country", "canonical": "United Arab Emirates"},
    "emiratos": {"type": "country", "canonical": "United Arab Emirates"},
    "uae": {"type": "country", "canonical": "United Arab Emirates"},
    "united arab emirates": {"type": "country", "canonical": "United Arab Emirates"},
    "jordania": {"type": "country", "canonical": "Jordan"},
    "jordan": {"type": "country", "canonical": "Jordan"},
    "qatar": {"type": "country", "canonical": "Qatar"},
    "oman": {"type": "country", "canonical": "Oman"},
    "omán": {"type": "country", "canonical": "Oman"},
    "turquia": {"type": "country", "canonical": "Turkey"},
    "turquía": {"type": "country", "canonical": "Turkey"},
    "turkey": {"type": "country", "canonical": "Turkey"},

    # States & Subdivisions
    "california": {"type": "state", "canonical": "California"},
    "texas": {"type": "state", "canonical": "Texas"},
    "florida": {"type": "state", "canonical": "Florida"},
    "nueva york": {"type": "state", "canonical": "New York"},
    "new york": {"type": "state", "canonical": "New York"},
    "washington": {"type": "state", "canonical": "Washington"},
    "illinois": {"type": "state", "canonical": "Illinois"},
    "colorado": {"type": "state", "canonical": "Colorado"},
    "nevada": {"type": "state", "canonical": "Nevada"},
    "arizona": {"type": "state", "canonical": "Arizona"},
    "pensilvania": {"type": "state", "canonical": "Pennsylvania"},
    "pennsylvania": {"type": "state", "canonical": "Pennsylvania"},
    "sao paulo": {"type": "state", "canonical": "São Paulo"},
    "são paulo": {"type": "state", "canonical": "São Paulo"},
    "buenos aires": {"type": "state", "canonical": "Buenos Aires"},
    "antofagasta": {"type": "state", "canonical": "Antofagasta"},
    "santiago": {"type": "state", "canonical": "Santiago"},
    "bavaria": {"type": "state", "canonical": "Bavaria"},
    "baviera": {"type": "state", "canonical": "Bavaria"},
    "madrid": {"type": "state", "canonical": "Madrid"},
    "cataluna": {"type": "state", "canonical": "Cataluña"},
    "cataluña": {"type": "state", "canonical": "Cataluña"},
    "andalucia": {"type": "state", "canonical": "Andalucía"},
    "andalucía": {"type": "state", "canonical": "Andalucía"},
    "new south wales": {"type": "state", "canonical": "New South Wales"},
    "queensland": {"type": "state", "canonical": "Queensland"},
    "victoria": {"type": "state", "canonical": "Victoria"},
    "western australia": {"type": "state", "canonical": "Western Australia"}
}

DEFAULT_AREA_ID = "europe"

def get_area_territory(area_id: Optional[str] = None, subdivision_name: Optional[str] = None) -> Dict[str, Any]:
    """Generates territory config dictionary for an Area of Interest or subdivision."""
    if not area_id or area_id not in AREAS_OF_INTEREST:
        return {
            "area_id": None,
            "area_name": "Global Overview",
            "name": "Global Canvas",
            "subdivision_name": None,
            "center": [20.0, 0.0],
            "zoom": 2.5,
            "bounds": [
                [-60.0, -170.0],
                [75.0, 175.0]
            ]
        }
    area = AREAS_OF_INTEREST[area_id]
    if subdivision_name and subdivision_name in area.get("subdivisions", {}):
        sub = area["subdivisions"][subdivision_name]
        return {
            "area_id": area["id"],
            "area_name": area["name"],
            "name": f"{sub['name']} ({area['name']})",
            "subdivision_name": sub["name"],
            "center": sub["center"],
            "zoom": sub["zoom"],
            "bounds": [
                [sub["center"][0] - 2.5, sub["center"][1] - 3.5],
                [sub["center"][0] + 2.5, sub["center"][1] + 3.5]
            ]
        }
    return {
        "area_id": area["id"],
        "area_name": area["name"],
        "name": area["name"],
        "subdivision_name": None,
        "center": area["center"],
        "zoom": area["zoom"],
        "bounds": area["bounds"]
    }

EMPTY_CONFIG: Dict[str, Any] = {
    "title": "General-Purpose GIS Architecture Template — Elsevier SoftwareX",
    "description": "Domain-Agnostic Conversational Spatial Search Sandbox. Select an Area of Interest and domain preset to begin.",
    "active_preset": None,
    "active_area": None,
    "active_subdivision": None,
    "territory": get_area_territory(None),
    "filter_fields": []
}

# Built-in Domain Presets (1-Click Switching)
PRESETS: Dict[str, Dict[str, Any]] = {
    "energy": {
        "title": "Renewable Energy & Power Grid Infrastructure",
        "description": "Exploration of utility-scale renewable generation, storage assets, and grid compliance.",
        "active_preset": "energy",
        "filter_fields": [
            {
                "key": "energy_type",
                "label": "Generation Technology",
                "type": "multiselect",
                "options": [
                    "Solar Photovoltaic",
                    "Onshore Wind",
                    "Offshore Wind",
                    "Hydroelectric Dam",
                    "Battery Storage (BESS)",
                    "Geothermal Plant"
                ],
                "colors": {
                    "Solar Photovoltaic": "#f59e0b",
                    "Onshore Wind": "#06b6d4",
                    "Offshore Wind": "#38bdf8",
                    "Hydroelectric Dam": "#3b82f6",
                    "Battery Storage (BESS)": "#8b5cf6",
                    "Geothermal Plant": "#10b981"
                },
                "synonyms": {
                    "solar photovoltaic": ["solar", "photovoltaic", "pv", "solar farm", "solar plant", "sun", "fotovoltaica"],
                    "onshore wind": ["onshore wind", "wind turbines", "wind farm", "wind", "turbines", "eolica", "aerogeneradores"],
                    "offshore wind": ["offshore wind", "marine wind", "sea wind", "coastal wind", "eolica marina"],
                    "hydroelectric dam": ["hydro", "hydroelectric", "dam", "reservoir", "water power", "hidroelectrica", "presa"],
                    "battery storage (bess)": ["battery", "storage", "bess", "battery storage", "energy storage", "baterias", "almacenamiento"],
                    "geothermal plant": ["geothermal", "thermal power", "geo", "hot springs", "geotermica"]
                }
            },
            {
                "key": "status",
                "label": "Operational Status",
                "type": "select",
                "options": [
                    "Operational",
                    "Under Construction",
                    "Permitting & Planned",
                    "Decommissioned"
                ],
                "colors": {
                    "Operational": "#10b981",
                    "Under Construction": "#f59e0b",
                    "Permitting & Planned": "#3b82f6",
                    "Decommissioned": "#64748b"
                },
                "synonyms": {
                    "operational": ["operational", "active", "online", "running", "producing", "commissioned", "operativo", "activo"],
                    "under construction": ["under construction", "construction", "building", "in progress", "en construccion"],
                    "permitting & planned": ["planned", "projected", "permitting", "proposed", "pipeline", "planificado", "proyecto"],
                    "decommissioned": ["decommissioned", "retired", "closed", "offline", "shut down", "cerrado"]
                }
            },
            {
                "key": "capacity_tier",
                "label": "Capacity Scale",
                "type": "select",
                "options": [
                    "Utility Scale (> 100 MW)",
                    "Medium Scale (20-100 MW)",
                    "Distributed (< 20 MW)"
                ],
                "colors": {
                    "Utility Scale (> 100 MW)": "#ec4899",
                    "Medium Scale (20-100 MW)": "#f97316",
                    "Distributed (< 20 MW)": "#14b8a6"
                },
                "synonyms": {
                    "utility scale (> 100 mw)": ["utility scale", "large scale", "major", "over 100", "> 100", "high capacity", "gran escala"],
                    "medium scale (20-100 mw)": ["medium scale", "mid scale", "20-100", "medium", "escala media"],
                    "distributed (< 20 mw)": ["distributed", "small scale", "local", "under 20", "< 20", "micro", "distribuida", "pequeña escala"]
                }
            },
            {
                "key": "esg_rating",
                "label": "ESG Compliance Grade",
                "type": "select",
                "options": [
                    "Grade A (Exemplary)",
                    "Grade B (Compliant)",
                    "Grade C (Under Review)"
                ],
                "colors": {
                    "Grade A (Exemplary)": "#10b981",
                    "Grade B (Compliant)": "#f59e0b",
                    "Grade C (Under Review)": "#ef4444"
                },
                "synonyms": {
                    "grade a (exemplary)": ["grade a", "esg a", "top esg", "exemplary", "tier a", "a", "grado a"],
                    "grade b (compliant)": ["grade b", "esg b", "compliant", "tier b", "b", "grado b"],
                    "grade c (under review)": ["grade c", "esg c", "under review", "tier c", "c", "grado c"]
                }
            }
        ]
    },
    "smartcity": {
        "title": "Smart City & Municipal Public Services",
        "description": "Urban planning dashboard monitoring municipal facilities, response priorities, and transit hubs.",
        "active_preset": "smartcity",
        "filter_fields": [
            {
                "key": "facility_type",
                "label": "Municipal Infrastructure",
                "type": "multiselect",
                "options": [
                    "General Hospital",
                    "Public School",
                    "Metro Transit Hub",
                    "Urban Green Park",
                    "Police Station",
                    "Fire & Rescue"
                ],
                "colors": {
                    "General Hospital": "#ef4444",
                    "Public School": "#f59e0b",
                    "Metro Transit Hub": "#3b82f6",
                    "Urban Green Park": "#10b981",
                    "Police Station": "#8b5cf6",
                    "Fire & Rescue": "#f97316"
                },
                "synonyms": {
                    "general hospital": ["hospital", "clinic", "health", "medical center", "emergency room", "care", "hospitales"],
                    "public school": ["school", "education", "college", "academy", "high school", "escuela", "colegio"],
                    "metro transit hub": ["metro", "transit", "station", "bus", "transport hub", "subway", "train", "transporte", "estacion"],
                    "urban green park": ["park", "green space", "garden", "urban park", "recreation", "parque", "jardin"],
                    "police station": ["police", "patrol", "precinct", "law enforcement", "station", "policia", "comisaria"],
                    "fire & rescue": ["fire", "firefighters", "rescue", "emergency station", "bomberos"]
                }
            },
            {
                "key": "service_status",
                "label": "Service Availability",
                "type": "select",
                "options": [
                    "Fully Operational (24/7)",
                    "Standard Hours",
                    "Limited Capacity",
                    "Emergency Maintenance"
                ],
                "colors": {
                    "Fully Operational (24/7)": "#10b981",
                    "Standard Hours": "#3b82f6",
                    "Limited Capacity": "#f59e0b",
                    "Emergency Maintenance": "#ef4444"
                },
                "synonyms": {
                    "fully operational (24/7)": ["24/7", "round the clock", "always open", "full service", "24 horas"],
                    "standard hours": ["standard hours", "business hours", "daytime", "horario estandar"],
                    "limited capacity": ["limited", "partial", "reduced", "capacidad reducida"],
                    "emergency maintenance": ["maintenance", "repair", "outage", "mantenimiento"]
                }
            },
            {
                "key": "priority_tier",
                "label": "Response Priority Tier",
                "type": "select",
                "options": [
                    "Critical Tier 1 (Emergency Core)",
                    "Essential Tier 2 (Public Key)",
                    "Community Tier 3 (Neighborhood)"
                ],
                "colors": {
                    "Critical Tier 1 (Emergency Core)": "#ef4444",
                    "Essential Tier 2 (Public Key)": "#f59e0b",
                    "Community Tier 3 (Neighborhood)": "#10b981"
                },
                "synonyms": {
                    "critical tier 1 (emergency core)": ["tier 1", "critical", "priority 1", "emergency core", "critico"],
                    "essential tier 2 (public key)": ["tier 2", "essential", "priority 2", "key service", "esencial"],
                    "community tier 3 (neighborhood)": ["tier 3", "community", "priority 3", "local service", "comunitario"]
                }
            }
        ]
    },
    "custom": {
        "title": "Custom User-Defined GIS Architecture Sandbox",
        "description": "Blank canvas. Use the Filter Studio to define custom dimensions and schema rules.",
        "active_preset": "custom",
        "filter_fields": []
    }
}

COLOR_PALETTE = [
    "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899",
    "#06b6d4", "#f97316", "#14b8a6", "#6366f1", "#84cc16"
]

def strip_accents(text: str) -> str:
    accents = {'á':'a', 'é':'e', 'í':'i', 'ó':'o', 'ú':'u', 'ñ':'n', 'ü':'u'}
    for k, v in accents.items():
        text = text.replace(k, v)
    return text

def get_word_variants(word: str) -> List[str]:
    w = word.strip().lower()
    variants = {w, strip_accents(w)}
    if w.endswith('es'):
        variants.add(w[:-2])
    elif w.endswith('s'):
        variants.add(w[:-1])
    else:
        variants.add(w + 's')
        variants.add(w + 'es')
    return [v for v in variants if len(v) >= 3]

# ==============================================================================
# PROCEDURAL OBJECT & DATASET GENERATOR (REAL-WORLD COORDINATES)
# ==============================================================================

def generate_procedural_points(
    count: int,
    config: Dict[str, Any],
    area_id: Optional[str] = None,
    subdivision_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Procedurally generates spatial facilities placed strictly on land within
    real-world geographic anchor coordinates belonging to the chosen Area of Interest
    and subdivision (state or country).
    """
    target_area_id = area_id or config.get("active_area") or DEFAULT_AREA_ID
    if target_area_id not in AREAS_OF_INTEREST:
        target_area_id = DEFAULT_AREA_ID

    area = AREAS_OF_INTEREST[target_area_id]
    subdivisions = area.get("subdivisions", {})

    target_sub = subdivision_name or config.get("active_subdivision")
    if target_sub and target_sub not in subdivisions:
        target_sub = None

    filter_fields = config.get("filter_fields", [])
    points: List[Dict[str, Any]] = []

    # Gather candidate anchors based on selection
    if target_sub:
        candidate_subs = [subdivisions[target_sub]]
    else:
        candidate_subs = list(subdivisions.values())

    if not candidate_subs:
        candidate_subs = list(AREAS_OF_INTEREST[DEFAULT_AREA_ID]["subdivisions"].values())

    for i in range(1, count + 1):
        chosen_sub = random.choice(candidate_subs)
        anchors = chosen_sub.get("anchors", [])
        if not anchors:
            anchor = {"name": chosen_sub["name"], "lat": chosen_sub["center"][0], "lon": chosen_sub["center"][1]}
        else:
            anchor = random.choice(anchors)

        # Apply moderate spatial jitter around realistic industrial/urban land anchors (~5 to 25 km)
        lat = round(anchor["lat"] + random.uniform(-0.065, 0.065), 5)
        lon = round(anchor["lon"] + random.uniform(-0.075, 0.075), 5)

        country = chosen_sub.get("country", chosen_sub["name"])
        state = anchor.get("state", chosen_sub["name"])
        zone = f"{state}, {country}" if state != country else country

        props: Dict[str, Any] = {}
        for f in filter_fields:
            key = f.get("key")
            opts = f.get("options", [])
            f_type = f.get("type", "select")
            if opts:
                if f_type == "multiselect" and random.random() < 0.25 and len(opts) > 1:
                    props[key] = random.sample(opts, k=min(2, len(opts)))
                else:
                    props[key] = random.choice(opts)

        first_field = filter_fields[0] if filter_fields else None
        first_val = props.get(first_field["key"]) if first_field else "Facility"
        if isinstance(first_val, list):
            first_val = first_val[0]

        hub_name = anchor["name"].split()[0]
        name = f"{hub_name} {first_val} #{i:02d}"

        # Generate descriptive sentence reflecting assigned attributes
        desc_parts = [f"{f.get('label', f.get('key'))}: {props.get(f.get('key'))}" for f in filter_fields if f.get("key") in props]
        if desc_parts:
            description = f"Located in {zone}. Key attributes: {'; '.join(desc_parts)}."
        else:
            description = f"Georeferenced asset in {zone} ({area['name']})."

        point = {
            "id": f"FAC-{i:03d}",
            "name": name,
            "latitude": lat,
            "longitude": lon,
            "country": country,
            "state": state,
            "zone": zone,
            "area": area["name"],
            "description": description,
            **props
        }
        points.append(point)

    return points


def load_dataset() -> List[Dict[str, Any]]:
    global _DATASET
    if not _DATASET:
        if DATA_FILE.exists():
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    _DATASET = json.load(f)
            except Exception:
                _DATASET = []
        else:
            _DATASET = []
    return _DATASET

def save_dataset(dataset: List[Dict[str, Any]]) -> None:
    global _DATASET
    _DATASET = dataset
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

def load_config() -> Dict[str, Any]:
    global _CONFIG
    if not _CONFIG:
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    _CONFIG = json.load(f)
            except Exception:
                _CONFIG = {}
        if not _CONFIG:
            _CONFIG = json.loads(json.dumps(EMPTY_CONFIG))
            save_config(_CONFIG)
    return _CONFIG

def save_config(new_config: Dict[str, Any]) -> None:
    global _CONFIG
    _CONFIG = new_config
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(new_config, f, indent=2, ensure_ascii=False)


# ==============================================================================
# STAGE 1 & 2: DYNAMIC CONVERSATIONAL NLU & DETERMINISTIC NORMALIZER
# ==============================================================================

def parse_conversational_query(query: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Translates raw conversational natural language into a validated filter dictionary
    matching dynamic user dimensions, geographic countries, states, and zones.
    """
    q_lower = query.lower()
    q_norm = strip_accents(q_lower)
    extracted_filters: Dict[str, Any] = {}
    matched_tokens: List[str] = []

    # Greeting / Help intent patterns
    greeting_patterns = [r'\bhello\b', r'\bhi\b', r'\bhey\b', r'\bgood morning\b', r'\bgreetings\b', r'\bhola\b', r'\bbuenos dias\b', r'\bayuda\b']
    help_patterns = [r'\bhelp\b', r'how (?:does it|to) work', r'what can you do', r'what is this', r'como funciona']
    is_greeting = any(re.search(pat, q_lower) for pat in greeting_patterns)
    is_help = any(re.search(pat, q_lower) for pat in help_patterns)

    # 1. Match Geographic Entities (Countries, States, Subdivisions)
    for alias_raw, info in GEOGRAPHIC_ALIASES.items():
        a_norm = strip_accents(alias_raw.lower())
        pattern = r'\b' + re.escape(a_norm) + r'\b'
        if re.search(pattern, q_norm):
            geo_type = info["type"]
            canonical = info["canonical"]
            if geo_type == "country":
                curr = extracted_filters.setdefault("country", [])
                if canonical not in curr:
                    curr.append(canonical)
            elif geo_type == "state":
                curr = extracted_filters.setdefault("state", [])
                if canonical not in curr:
                    curr.append(canonical)
            matched_tokens.append(alias_raw)

    # 2. Match each dynamic filter field defined by user
    filter_fields = config.get("filter_fields", [])
    for field in filter_fields:
        f_key = field.get("key")
        f_type = field.get("type", "select")
        options = field.get("options", [])
        synonyms = field.get("synonyms", {})

        field_matches: List[str] = []

        # Check explicit synonyms mapping
        for canon_opt, syn_list in synonyms.items():
            for syn in syn_list:
                s_norm = strip_accents(syn.lower())
                pattern = r'\b' + re.escape(s_norm) + r'\b'
                if re.search(pattern, q_norm):
                    matched_opt = next((opt for opt in options if strip_accents(opt.lower()) == strip_accents(canon_opt.lower())), canon_opt)
                    if matched_opt not in field_matches:
                        field_matches.append(matched_opt)
                    matched_tokens.append(syn)
                    break

        # Check literal option words and morphological variants only if no explicit synonym matched
        if not field_matches:
            STOP_WORDS = {"grade", "tier", "scale", "district", "facility", "plant", "hub", "station", "park", "center", "de", "la", "el", "en", "with", "and", "or", "the", "a", "an", "of", "in"}
            for opt in options:
                if opt in field_matches:
                    continue
                words = opt.split()
                matched = False
                for word in words:
                    if word.lower() in STOP_WORDS:
                        continue
                    for variant in get_word_variants(word):
                        pattern = r'\b' + re.escape(variant) + r'\b'
                        if re.search(pattern, q_norm):
                            field_matches.append(opt)
                            matched_tokens.append(word)
                            matched = True
                            break
                    if matched:
                        break

        if field_matches:
            if f_type == "multiselect" or len(field_matches) > 1:
                extracted_filters[f_key] = field_matches
            else:
                extracted_filters[f_key] = field_matches[0]

    # Intent determination
    if (is_greeting or is_help) and not extracted_filters:
        intent = "generic_qa"
    elif extracted_filters:
        intent = "filter_search"
    else:
        if any(w in q_lower for w in ["all", "everything", "dataset", "show all", "list all", "todos", "todas"]):
            intent = "filter_search"
        else:
            intent = "generic_qa"

    return {
        "intent": intent,
        "filters": extracted_filters,
        "matched_tokens": list(set(matched_tokens))
    }


# ==============================================================================
# STAGE 3: APACHE SOLR BOOLEAN QUERY BUILDER & SPATIAL FILTERING ENGINE
# ==============================================================================

def build_solr_query(filters: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Constructs Apache Solr search query parameters (q, fq) from structured filters.
    """
    q = "*:*"
    fq_list: List[str] = []

    for f_key, f_val in filters.items():
        if not f_val:
            continue
        if isinstance(f_val, list):
            clauses = [f'"{v}"' for v in f_val]
            fq_list.append(f"{f_key}:({' OR '.join(clauses)})")
        else:
            fq_list.append(f'{f_key}:"{f_val}"')

    solr_url_preview = f"/solr/select?q={q}" + "".join([f"&fq={rule}" for rule in fq_list])

    return {
        "q": q,
        "fq": fq_list,
        "solr_url_preview": solr_url_preview
    }


def execute_spatial_filtering(filters: Dict[str, Any], dataset: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes Solr boolean filter rules over the in-memory dataset,
    computing dynamic multidimensional facet distributions.
    """
    matched_sites = []

    for site in dataset:
        matches = True
        for f_key, f_val in filters.items():
            if not f_val:
                continue
            site_val = site.get(f_key)
            if site_val is None:
                matches = False
                break

            target_vals = [strip_accents(str(v).lower()) for v in (f_val if isinstance(f_val, list) else [f_val])]

            if isinstance(site_val, list):
                site_vals_norm = [strip_accents(str(x).lower()) for x in site_val]
                if not any(tv in site_vals_norm for tv in target_vals):
                    matches = False
                    break
            else:
                site_val_norm = strip_accents(str(site_val).lower())
                if site_val_norm not in target_vals:
                    matches = False
                    break

        if matches:
            site_copy = dict(site)
            site_copy["score"] = 0.98 if filters else 0.85
            matched_sites.append(site_copy)

    # Compute live Solr facets for all user filter fields + geographic dimensions
    facets: Dict[str, Dict[str, int]] = {
        "country": {},
        "state": {}
    }

    # Geographic Facets
    for doc in matched_sites:
        c = doc.get("country")
        if c:
            facets["country"][c] = facets["country"].get(c, 0) + 1
        s = doc.get("state")
        if s:
            facets["state"][s] = facets["state"].get(s, 0) + 1

    # Dynamic Filter Fields Facets
    for f in config.get("filter_fields", []):
        f_key = f["key"]
        options = f.get("options", [])
        facets[f_key] = {opt: 0 for opt in options}

        for doc in matched_sites:
            val = doc.get(f_key)
            if isinstance(val, list):
                for item in val:
                    norm_item = next((opt for opt in options if opt.lower() == str(item).lower()), str(item))
                    facets[f_key][norm_item] = facets[f_key].get(norm_item, 0) + 1
            elif val is not None:
                norm_val = next((opt for opt in options if opt.lower() == str(val).lower()), str(val))
                facets[f_key][norm_val] = facets[f_key].get(norm_val, 0) + 1

    return {
        "matched_docs": matched_sites,
        "matched_ids": [d["id"] for d in matched_sites],
        "num_found": len(matched_sites),
        "total_dataset": len(dataset),
        "facets": facets
    }


# ==============================================================================
# STAGE 4: GROUNDED NARRATIVE SYNTHESIS
# ==============================================================================

def generate_natural_narrative(
    query: str,
    intent: str,
    filters: Dict[str, Any],
    results: Dict[str, Any],
    config: Dict[str, Any]
) -> str:
    """
    Synthesizes a grounded natural language response in English explaining spatial query results.
    """
    num_found = results.get("num_found", 0)
    total = results.get("total_dataset", len(load_dataset()))
    docs = results.get("matched_docs", [])
    territory_name = config.get("territory", {}).get("name", "the selected area")

    if not config.get("active_preset"):
        return (
            f"### 👋 Welcome to the Decoupled GIS Architecture Sandbox\n\n"
            f"Currently, **no domain is selected**.\n\n"
            f"#### 🚀 Getting Started:\n"
            f"1. **Select an Area of Interest**: USA 🇺🇸, South America 🌎, Europe 🇪🇺, Middle East 🏜️, or Southeast Asia & Oceania 🌏.\n"
            f"2. **Select a Domain Preset**: *⚡ Renewable Energy*, *🏙️ Smart City*, or *✨ Custom*.\n"
            f"3. Click **🎲 Generate Points** to scatter real-coordinate facilities with automatic Country and State tags.\n"
            f"4. Perform **conversational searches** (e.g. *\"solar in Australia\"*, *\"wind in California\"*) to synchronize the map in real time."
        )

    if total == 0:
        return (
            f"👋 **{territory_name} GIS Sandbox Ready (0 facilities loaded).**\n\n"
            f"### 🚀 Next Step:\n"
            f"Choose the number of facilities and click **\"🎲 Generate Points\"**.\n"
            f"The procedural generator will distribute points across **{territory_name}** with real GPS coordinates, "
            f"identifying the exact country, state, and domain attributes for each facility."
        )

    if intent == "generic_qa" and not filters:
        return (
            f"👋 **{territory_name} GIS Sandbox Active ({total} facilities loaded).**\n\n"
            f"This sandbox demonstrates how our decoupled 4-stage architecture (**Conversational NLU $\\to$ Solr Boolean Builder $\\to$ Leaflet GIS Visual Sync**) "
            f"adapts dynamically to real-world geospatial domains.\n\n"
            f"### 💡 Things you can try right now:\n"
            f"- **Conversational Search**: Type queries such as *\"Solar farms in California\"*, *\"Battery storage in Australia\"*, or *\"Operational facilities with Grade A\"*.\n"
            f"- **Manual Facet Controls**: Click any pill badge on the sidebar to filter Solr rules.\n"
            f"- **Inspector Drawer**: Open the bottom drawer to examine NLU tokenization, JSON schema, and Solr `$fq` rules."
        )

    if num_found == 0:
        return (
            f"🔍 **No spatial facilities matched your active criteria in {territory_name}:**\n"
            f"No objects satisfy all active filter rules simultaneously.\n\n"
            f"💡 *Suggestion: Click on an active filter badge to relax criteria or try another technology/region.*"
        )

    fields = config.get("filter_fields", [])
    primary_field = fields[0]["key"] if fields else "country"
    field_label = fields[0].get("label", primary_field) if fields else "Country"

    summary: Dict[str, int] = {}
    country_summary: Dict[str, int] = {}
    for d in docs:
        val = d.get(primary_field)
        if isinstance(val, list):
            val = ", ".join(val)
        summary[str(val)] = summary.get(str(val), 0) + 1
        c = d.get("country", territory_name)
        country_summary[c] = country_summary.get(c, 0) + 1

    summary_str = ", ".join([f"{k} ({v})" for k, v in summary.items()])
    countries_str = ", ".join([f"{k} ({v})" for k, v in country_summary.items()])
    featured = docs[0]

    pct = round(num_found / total * 100, 1) if total else 100
    narrative = (
        f"✅ **Identified {num_found} of {total} facilities ({pct}%) in {territory_name}:**\n\n"
        f"- 📌 **Breakdown by {field_label}**: {summary_str}.\n"
        f"- 🌍 **Countries / Regions**: {countries_str}.\n"
        f"- 🌟 **Featured Facility**: **{featured.get('name')}** (Location: *{featured.get('zone', featured.get('country'))}*).\n\n"
        f"*(Matching facilities are highlighted on the real-world Leaflet map with pulsing radar rings and active filter tags).* "
    )
    return narrative


# ==============================================================================
# PIPELINE ORCHESTRATOR
# ==============================================================================

def process_query_pipeline(payload: Dict[str, Any]) -> Dict[str, Any]:
    dataset = load_dataset()
    config = load_config()

    query = payload.get("query", "").strip()
    manual_filters = payload.get("manual_filters")

    if manual_filters is not None and isinstance(manual_filters, dict):
        validated_filters = {k: v for k, v in manual_filters.items() if v}
        intent = "filter_search"
        matched_tokens = list(validated_filters.keys())
    elif query:
        parsed = parse_conversational_query(query, config)
        validated_filters = parsed["filters"]
        intent = parsed["intent"]
        matched_tokens = parsed["matched_tokens"]
    else:
        validated_filters = {}
        intent = "generic_qa"
        matched_tokens = []

    solr_query = build_solr_query(validated_filters, config)
    filtering_results = execute_spatial_filtering(validated_filters, dataset, config)

    # Active filter badges for UI map header
    active_badges = []
    fields_dict = {f["key"]: f for f in config.get("filter_fields", [])}
    for k, v in validated_filters.items():
        if not v:
            continue
        if k == "country":
            label = "Country"
        elif k == "state":
            label = "State / Subdivision"
        elif k == "zone":
            label = "Geographic Zone"
        else:
            f_def = fields_dict.get(k, {})
            label = f_def.get("label", k.title())

        vals = v if isinstance(v, list) else [str(v)]
        active_badges.append({"key": k, "label": label, "values": vals})

    narrative = generate_natural_narrative(query, intent, validated_filters, filtering_results, config)

    return {
        "query": query,
        "intent": intent,
        "matched_tokens": matched_tokens,
        "filters": validated_filters,
        "solr_query": solr_query,
        "solr_facets": filtering_results["facets"],
        "num_found": filtering_results["num_found"],
        "total_dataset": filtering_results["total_dataset"],
        "matched_ids": filtering_results["matched_ids"],
        "active_map_filters": active_badges,
        "docs": filtering_results["matched_docs"],
        "narrative": narrative,
        "response_text": narrative
    }


# ==============================================================================
# HTTP WEB SERVER & REST API HANDLER
# ==============================================================================

class GenericGISHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        # API: Return all facilities / points
        if self.path in ["/api/facilities", "/api/points", "/api/sites", "/api/data"]:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = load_dataset()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        # API: Return active configuration
        elif self.path in ["/api/config", "/api/schema", "/api/filters_config"]:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            cfg = load_config()
            self.wfile.write(json.dumps(cfg, ensure_ascii=False).encode("utf-8"))
            return

        # API: Return catalog of Areas of Interest (AOIs)
        elif self.path in ["/api/areas", "/api/areas_of_interest"]:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            # Serialize areas catalog without heavy internal anchor points
            serialized_areas = {}
            for aid, ainfo in AREAS_OF_INTEREST.items():
                subs_summary = {}
                for sname, sinfo in ainfo.get("subdivisions", {}).items():
                    subs_summary[sname] = {
                        "name": sinfo["name"],
                        "code": sinfo.get("code", ""),
                        "country": sinfo.get("country", sinfo["name"]),
                        "center": sinfo["center"],
                        "zoom": sinfo["zoom"],
                        "anchors_count": len(sinfo.get("anchors", []))
                    }
                serialized_areas[aid] = {
                    "id": ainfo["id"],
                    "name": ainfo["name"],
                    "icon": ainfo["icon"],
                    "center": ainfo["center"],
                    "zoom": ainfo["zoom"],
                    "bounds": ainfo["bounds"],
                    "description": ainfo["description"],
                    "subdivisions_type": ainfo.get("subdivisions_type", "Subdivision"),
                    "subdivisions": subs_summary
                }
            self.wfile.write(json.dumps(serialized_areas, ensure_ascii=False).encode("utf-8"))
            return

        # API: Health check
        elif self.path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {
                "status": "ok",
                "app": "General GIS Template Sandbox",
                "points_count": len(load_dataset()),
                "filters_count": len(load_config().get("filter_fields", []))
            }
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        return super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        # API: Conversational query or manual filter query
        if self.path in ["/api/chat", "/api/query"]:
            try:
                payload = json.loads(post_data) if post_data else {}
                result = process_query_pipeline(payload)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # API: Switch active Area of Interest or Subdivision
        elif self.path in ["/api/set_area", "/api/area"]:
            try:
                payload = json.loads(post_data) if post_data else {}
                area_id = payload.get("area", DEFAULT_AREA_ID)
                subdivision_name = payload.get("subdivision")

                if area_id not in AREAS_OF_INTEREST:
                    raise ValueError(f"Unknown area_id: {area_id}")

                cfg = load_config()
                cfg["active_area"] = area_id
                cfg["active_subdivision"] = subdivision_name
                cfg["territory"] = get_area_territory(area_id, subdivision_name)
                save_config(cfg)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "active_area": area_id,
                    "active_subdivision": subdivision_name,
                    "territory": cfg["territory"],
                    "config": cfg
                }, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # API: Generate procedural random points across the chosen Area of Interest
        elif self.path == "/api/generate_points":
            try:
                payload = json.loads(post_data) if post_data else {}
                count = int(payload.get("count", 40))
                count = max(10, min(150, count))
                area_id = payload.get("area")
                subdivision_name = payload.get("subdivision")

                cfg = load_config()
                if area_id and area_id in AREAS_OF_INTEREST:
                    cfg["active_area"] = area_id
                    cfg["active_subdivision"] = subdivision_name
                    cfg["territory"] = get_area_territory(area_id, subdivision_name)
                    save_config(cfg)

                new_points = generate_procedural_points(count, cfg, area_id=area_id, subdivision_name=subdivision_name)
                save_dataset(new_points)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "count": len(new_points),
                    "area": cfg.get("active_area"),
                    "subdivision": cfg.get("active_subdivision"),
                    "points": new_points
                }, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # API: Clear all points from the map
        elif self.path == "/api/clear_points":
            try:
                save_dataset([])
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "count": 0}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # API: Add new user-defined filter field
        elif self.path == "/api/add_filter":
            try:
                payload = json.loads(post_data)
                label = payload.get("label", "").strip()
                if not label:
                    raise ValueError("Filter name cannot be empty.")

                raw_key = payload.get("key") or label.lower()
                key = re.sub(r'[^a-zA-Z0-9_]', '_', strip_accents(raw_key.lower()))

                options = [opt.strip() for opt in payload.get("options", []) if opt.strip()]
                if not options:
                    options = ["Option A", "Option B", "Option C"]

                colors = {}
                for idx, opt in enumerate(options):
                    colors[opt] = COLOR_PALETTE[idx % len(COLOR_PALETTE)]

                cfg = load_config()
                existing = next((f for f in cfg.get("filter_fields", []) if f["key"] == key), None)
                field_entry = {
                    "key": key,
                    "label": label,
                    "type": payload.get("type", "select"),
                    "options": options,
                    "colors": colors,
                    "synonyms": {}
                }

                if existing:
                    existing.update(field_entry)
                else:
                    cfg.setdefault("filter_fields", []).append(field_entry)

                save_config(cfg)

                # Populate property on existing points if any
                dataset = load_dataset()
                for pt in dataset:
                    if key not in pt or not pt[key]:
                        pt[key] = random.choice(options)
                save_dataset(dataset)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "field": field_entry, "config": cfg}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # API: Delete filter field
        elif self.path == "/api/delete_filter":
            try:
                payload = json.loads(post_data)
                key = payload.get("key", "").strip()
                cfg = load_config()
                cfg["filter_fields"] = [f for f in cfg.get("filter_fields", []) if f["key"] != key]
                save_config(cfg)

                dataset = load_dataset()
                for pt in dataset:
                    pt.pop(key, None)
                save_dataset(dataset)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "config": cfg}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # API: Add an option to an existing filter field
        elif self.path == "/api/add_option":
            try:
                payload = json.loads(post_data)
                key = payload.get("key")
                option = payload.get("option", "").strip()
                if not option:
                    raise ValueError("Option value cannot be empty.")

                cfg = load_config()
                field = next((f for f in cfg.get("filter_fields", []) if f["key"] == key), None)
                if not field:
                    raise ValueError(f"Filter with key '{key}' not found.")

                if option not in field["options"]:
                    field["options"].append(option)
                    if "colors" not in field:
                        field["colors"] = {}
                    field["colors"][option] = COLOR_PALETTE[len(field["options"]) % len(COLOR_PALETTE)]
                    save_config(cfg)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "field": field}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # API: Switch Preset (energy, smartcity, custom) without auto-generating points
        elif self.path == "/api/preset":
            try:
                payload = json.loads(post_data)
                preset_id = payload.get("preset", "energy")
                generate = payload.get("generate", False)
                count = int(payload.get("count", 40))

                if preset_id not in PRESETS:
                    raise ValueError(f"Unknown preset: {preset_id}")

                cfg = load_config()
                active_area = cfg.get("active_area")
                active_sub = cfg.get("active_subdivision")

                new_cfg = json.loads(json.dumps(PRESETS[preset_id]))
                new_cfg["active_area"] = active_area
                new_cfg["active_subdivision"] = active_sub
                new_cfg["territory"] = get_area_territory(active_area, active_sub)
                save_config(new_cfg)

                if generate:
                    new_points = generate_procedural_points(count, new_cfg, area_id=active_area, subdivision_name=active_sub)
                    save_dataset(new_points)
                else:
                    new_points = []
                    save_dataset(new_points)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "preset": preset_id,
                    "config": new_cfg,
                    "points": new_points
                }, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # API: Save raw configuration
        elif self.path in ["/api/config", "/api/schema", "/api/filters_config"]:
            try:
                new_cfg = json.loads(post_data)
                save_config(new_cfg)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "saved", "config": new_cfg}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # API: Reset to factory defaults (empty map and no domain selected)
        elif self.path == "/api/reset":
            try:
                new_cfg = json.loads(json.dumps(EMPTY_CONFIG))
                save_config(new_cfg)
                save_dataset([])

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "reset_successful",
                    "config": new_cfg,
                    "points": []
                }, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()


def run_server(port: int = 8085, host: str = "0.0.0.0"):
    # Ensure dataset file and config file exist
    load_config()
    load_dataset()

    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, GenericGISHandler)
    print(f"==========================================================================")
    print(f" 🚀 General-Purpose GIS Architecture Template — Elsevier SoftwareX")
    print(f" 🗺️  World Basemap & 5 Areas of Interest (USA, South America, Europe, Middle East, SE Asia/Oceania)")
    print(f" 🌐 Server running at: http://localhost:{port}")
    print(f"==========================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Shutting down server.")
        httpd.server_close()


def main():
    parser = argparse.ArgumentParser(description="Run General-Purpose GIS Architecture Template Server")
    parser.add_argument("--port", type=int, default=8085, help="HTTP Port (default: 8085)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Binding host (default: 0.0.0.0)")
    args = parser.parse_args()
    run_server(port=args.port, host=args.host)


if __name__ == "__main__":
    main()
