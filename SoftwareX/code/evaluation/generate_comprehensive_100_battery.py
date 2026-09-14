#!/usr/bin/env python3
"""
generate_comprehensive_100_battery.py
Constructs a balanced 100-test case benchmark suite for CRMs Data Space:
- 20 Canonical slot-filling queries (baseline)
- 20 Negation and exclusion queries (negation handling)
- 20 Semantic domain expansion & implicit association queries (reasoning)
- 20 Multi-intent, technical standards (UNFC/JORC) and conceptual QA queries (intent classification)
- 20 Noisy, colloquial, typo-ridden & chemical symbol queries (real-world robustness)
"""

import json
from pathlib import Path

OUTPUT_FILE = Path(__file__).resolve().parent / "test_battery_100.json"

test_cases = []

# =========================================================================
# Category 1: Canonical Slot-Filling (20 queries)
# =========================================================================
cat1 = [
    ("Muestra escombreras de lithium en Spain", ["spain"], ["lithium"], ["waste dump"], []),
    ("Find active cobalt tailings storage facilities in Portugal", ["portugal"], ["cobalt"], ["tailings storage facility"], ["active"]),
    ("Depósitos de tungsten y tin en Germany", ["germany"], ["tungsten", "tin"], [], []),
    ("Balsas de rare earth elements inactivas en France", ["france"], ["rare earth elements"], ["pond", "tailings storage facility"], ["inactive"]),
    ("Active nickel dumps in Sweden and Italy", ["sweden", "italy"], ["nickel"], ["waste dump"], ["active"]),
    ("Muestra escombreras de copper en Finland", ["finland"], ["copper"], ["waste dump"], []),
    ("Find active tin tailings storage facilities in Poland", ["poland"], ["tin"], ["tailings storage facility"], ["active"]),
    ("Depósitos de tantalum y manganese en Italy", ["italy"], ["tantalum", "manganese"], [], []),
    ("Balsas de graphite inactivas en Greece y Czechia", ["greece", "czechia"], ["graphite"], ["pond", "tailings storage facility"], ["inactive"]),
    ("Active titanium dumps in Ireland and Spain", ["ireland", "spain"], ["titanium"], ["waste dump"], ["active"]),
    ("Muestra escombreras de pge en Austria", ["austria"], ["pge"], ["waste dump"], []),
    ("Find active manganese tailings storage facilities in Czechia", ["czechia"], ["manganese"], ["tailings storage facility"], ["active"]),
    ("Depósitos de lithium y nickel en Spain", ["spain"], ["lithium", "nickel"], [], []),
    ("Balsas de cobalt inactivas en Portugal y Sweden", ["portugal", "sweden"], ["cobalt"], ["pond", "tailings storage facility"], ["inactive"]),
    ("Active tungsten dumps in Germany and Finland", ["germany", "finland"], ["tungsten"], ["waste dump"], ["active"]),
    ("Muestra escombreras de rare earth elements en France", ["france"], ["rare earth elements"], ["waste dump"], []),
    ("Find active nickel tailings storage facilities in Sweden", ["sweden"], ["nickel"], ["tailings storage facility"], ["active"]),
    ("Depósitos de copper y cobalt en Poland", ["poland"], ["copper", "cobalt"], [], []),
    ("Balsas de tin inactivas en Spain e Italy", ["spain", "italy"], ["tin"], ["pond", "tailings storage facility"], ["inactive"]),
    ("Active tantalum dumps in Ireland and Greece", ["ireland", "greece"], ["tantalum"], ["waste dump"], ["active"])
]

for q, co, cm, st, ps in cat1:
    test_cases.append({
        "id": f"TC-{len(test_cases)+1:03d}",
        "category": "canonical_slot_filling",
        "query": q,
        "expected_intent": "filter_search",
        "expected_filters": {
            "countries": co,
            "commodities": cm,
            "storage_facility_types": st,
            "project_status": ps
        }
    })

# =========================================================================
# Category 2: Negations and Exclusions (20 queries)
# =========================================================================
cat2 = [
    ("Muestra balsas de litio en Europa pero que no estén en España", [], ["lithium"], ["pond", "tailings storage facility"], []),
    ("Find active cobalt tailings storage facilities not in Portugal", [], ["cobalt"], ["tailings storage facility"], ["active"]),
    ("Depósitos de tungsten en Germany sin incluir estaño", ["germany"], ["tungsten"], [], []),
    ("Balsas de tierras raras en France excluyendo instalaciones inactivas", ["france"], ["rare earth elements"], ["pond", "tailings storage facility"], ["active"]),
    ("Active dumps in Sweden excluding nickel", ["sweden"], [], ["waste dump"], ["active"]),
    ("Escombreras de cobre en Europa que no se encuentren en Finlandia", [], ["copper"], ["waste dump"], []),
    ("Tailings storage facilities in Poland without tin", ["poland"], [], ["tailings storage facility"], []),
    ("Depósitos en Italy que no contengan tantalum ni manganeso", ["italy"], [], [], []),
    ("Balsas en Grecia y Chequia pero que no sean de grafito", ["greece", "czechia"], [], ["pond", "tailings storage facility"], []),
    ("Dumps in Ireland and Spain excluding titanium", ["ireland", "spain"], [], ["waste dump"], []),
    ("Escombreras en Austria pero que no tengan platino ni PGE", ["austria"], [], ["waste dump"], []),
    ("Tailings facilities in Czechia that are not active", ["czechia"], [], ["tailings storage facility"], ["inactive"]),
    ("Depósitos de litio en la UE pero sin incluir instalaciones en España", [], ["lithium"], [], []),
    ("Balsas de cobalto en Portugal que no estén abandonadas ni inactivas", ["portugal"], ["cobalt"], ["pond", "tailings storage facility"], ["active"]),
    ("Dumps in Germany excluding tungsten", ["germany"], [], ["waste dump"], []),
    ("Instalaciones de tierras raras en Europa pero no en Francia", [], ["rare earth elements"], [], []),
    ("Tailings storage facilities in Sweden without nickel", ["sweden"], [], ["tailings storage facility"], []),
    ("Depósitos en Polonia con cobre pero sin cobalto", ["poland"], ["copper"], [], []),
    ("Balsas de estaño que no estén ubicadas en Italia", [], ["tin"], ["pond", "tailings storage facility"], []),
    ("Active dumps excluding tantalum in Ireland", ["ireland"], [], ["waste dump"], ["active"])
]

for q, co, cm, st, ps in cat2:
    test_cases.append({
        "id": f"TC-{len(test_cases)+1:03d}",
        "category": "negations_and_exclusions",
        "query": q,
        "expected_intent": "filter_search",
        "expected_filters": {
            "countries": co,
            "commodities": cm,
            "storage_facility_types": st,
            "project_status": ps
        }
    })

# =========================================================================
# Category 3: Semantic Association & Domain Expansion (20 queries)
# =========================================================================
cat3 = [
    ("Depósitos con materiales para baterías de vehículos eléctricos en Finlandia", ["finland"], ["lithium", "cobalt", "nickel", "graphite"], [], []),
    ("Minerales críticos para imanes permanentes de aerogeneradores en Suecia", ["sweden"], ["rare earth elements"], [], []),
    ("Instalaciones mineras en la Península Ibérica con litio", ["spain", "portugal"], ["lithium"], [], []),
    ("Residuos mineros en los países nórdicos con cobre", ["sweden", "finland"], ["copper"], [], []),
    ("Metales refractarios para aleaciones aeroespaciales en Alemania", ["germany"], ["tungsten", "tantalum", "titanium"], [], []),
    ("Depósitos con elementos para catalizadores de hidrógeno y pilas de combustible en Austria", ["austria"], ["pge"], [], []),
    ("Secondary raw materials for lithium-ion battery cathode manufacturing in Poland", ["poland"], ["lithium", "cobalt", "nickel"], [], []),
    ("Critical minerals for offshore wind turbine generators in France", ["france"], ["rare earth elements"], [], []),
    ("Extractive waste facilities in the Iberian Peninsula with cobalt", ["spain", "portugal"], ["cobalt"], [], []),
    ("Mining tailings in Scandinavia containing nickel", ["sweden", "finland"], ["nickel"], ["tailings storage facility"], []),
    ("High-density refractory metals in Czechia waste dumps", ["czechia"], ["tungsten", "tantalum"], ["waste dump"], []),
    ("Electrolyzer catalyst metals in German mining residues", ["germany"], ["pge"], [], []),
    ("Yacimientos con materias primas para almacenamiento energético electroquímico en España", ["spain"], ["lithium", "cobalt", "nickel", "graphite"], [], []),
    ("Instalaciones en el arco atlántico ibérico con estaño y wolframio", ["spain", "portugal"], ["tin", "tungsten"], [], []),
    ("Mining waste containing battery anode materials in Sweden", ["sweden"], ["graphite", "lithium"], [], []),
    ("Photovoltaic and semiconductor related critical metals in Italy", ["italy"], ["copper", "tin"], [], []),
    ("Depósitos de residuos mineros en Europa Central con manganeso", ["germany", "austria", "czechia", "poland"], ["manganese"], [], []),
    ("Heavy rare earth magnet feedstock facilities in Sweden", ["sweden"], ["rare earth elements"], [], []),
    ("Extractive waste sites in southern European countries with titanium", ["spain", "portugal", "italy", "greece"], ["titanium"], [], []),
    ("Green transition strategic raw materials impoundments in Finland", ["finland"], ["lithium", "cobalt", "nickel"], [], [])
]

for q, co, cm, st, ps in cat3:
    test_cases.append({
        "id": f"TC-{len(test_cases)+1:03d}",
        "category": "semantic_association_expansion",
        "query": q,
        "expected_intent": "filter_search",
        "expected_filters": {
            "countries": co,
            "commodities": cm,
            "storage_facility_types": st,
            "project_status": ps
        }
    })

# =========================================================================
# Category 4: Technical Standards & Conceptual QA (UNFC, JORC, Safety) (20 queries)
# =========================================================================
cat4 = [
    "¿Qué criterios establece el marco UNFC 2019 para la clasificación de recursos antropogénicos en escombreras?",
    "¿Cómo se reportan los recursos minerales en depósitos de relaves según los códigos JORC y NI 43-101?",
    "¿Qué diferencia técnica existe entre una balsa de decantación (tailings pond) y una escombrera de roca estéril (waste dump)?",
    "¿Cuáles son los riesgos ambientales más críticos asociados a la licuefacción estática en presas de relaves aguas arriba?",
    "Explícame qué es el drenaje ácido de mina (AMD) y qué medidas de restauración pasiva existen",
    "¿Cuál es la normativa europea sobre gestión de residuos de las industrias extractivas (Directiva 2006/21/CE)?",
    "Hola, ¿cómo puede ayudarme esta plataforma a explorar el espacio de datos de materias primas críticas?",
    "¿Qué significa la clasificación E1-F2-G1 en el sistema de las Naciones Unidas (UNFC)?",
    "¿Cómo se calcula el balance hídrico y la estabilidad de taludes en balsas de lodos mineros?",
    "What are the core reporting principles required under the JORC Code for secondary mineral reserves?",
    "How does the UNFC Framework harmonize anthropogenic resource inventories across EU member states?",
    "What is the technical distinction between upstream, downstream, and centerline tailings dam designs?",
    "Can you explain the biogeochemical mechanisms of acid mine drainage generation in sulfidic waste dumps?",
    "What environmental monitoring technologies are deployed for satellite InSAR tailings dam deformation?",
    "Good morning, can you provide guidance on how to use this cartographic Data Space platform?",
    "¿Qué directivas de la Ley Europea de Materias Primas Fundamentales (CRMA) regulan el reciclaje de residuos mineros?",
    "¿Cómo evalúa el código SAMREC la viabilidad técnico-económica de retratar relaves antiguos?",
    "¿Qué precauciones geotécnicas son necesarias antes de iniciar la restauración de una escombrera inerte?",
    "Help me understand the spatial data architecture and Leaflet GIS integration used in this system",
    "What chemical processes are used in the hydrometallurgical recovery of cobalt and lithium from tailings?"
]

for q in cat4:
    test_cases.append({
        "id": f"TC-{len(test_cases)+1:03d}",
        "category": "technical_standards_and_qa",
        "query": q,
        "expected_intent": "generic_qa",
        "expected_filters": {
            "countries": [],
            "commodities": [],
            "storage_facility_types": [],
            "project_status": []
        }
    })

# =========================================================================
# Category 5: Noisy, Colloquial, Multilingual & Chemical Symbols (20 queries)
# =========================================================================
cat5 = [
    ("hola buenas tardes, me gustaría saber si tenéis registrado algún depósito de W o Sn en Ourense", ["spain"], ["tungsten", "tin"], [], []),
    ("escombreras de golfranio y tántalo activas en galiza", ["spain"], ["tungsten", "tantalum"], ["waste dump"], ["active"]),
    ("hay balsas de decantacion operativas con Li y Co en portugal?", ["portugal"], ["lithium", "cobalt"], ["pond", "tailings storage facility"], ["active"]),
    ("proyectos mineros en salamanca que esten parados o en mantenimiento", ["spain"], [], [], ["inactive", "care and maintenance"]),
    ("vertederos y acopios con nikel y manganeso en suecia", ["sweden"], ["nickel", "manganese"], ["waste dump", "stockpile"], []),
    ("balsas de relave abandonadas en andalucia con presencia de cobre", ["spain"], ["copper"], ["pond", "tailings storage facility"], ["inactive"]),
    ("quisiera consultar instalaciones de tierras raras (REE) en francia que no esten restauradas", ["france"], ["rare earth elements"], [], []),
    ("tailings impoundments in Ireland with acid water seepage", ["ireland"], [], ["pond", "tailings storage facility"], []),
    ("acopios de mineral de titanio y niobio en italia", ["italy"], ["titanium", "tantalum"], ["stockpile"], []),
    ("dime todas las balsas de relaves en grecia y chequia", ["greece", "czechia"], [], ["pond", "tailings storage facility"], []),
    ("depósitos de W en Ourense y Zamora", ["spain"], ["tungsten"], [], []),
    ("escombreras inertes de granito en galicia", ["spain"], [], ["waste dump"], []),
    ("balsas con lodos y barros de decantación en castilla y león", ["spain"], [], ["pond", "tailings storage facility"], []),
    ("instalaciones mineras en el sur de la península con cobre", ["spain"], ["copper"], [], []),
    ("show me old inactive Cu and Ni tailings dumps in Sweden", ["sweden"], ["copper", "nickel"], ["waste dump", "tailings storage facility"], ["inactive"]),
    ("are there any operating Li or Ta ponds in northern Portugal?", ["portugal"], ["lithium", "tantalum"], ["pond", "tailings storage facility"], ["active"]),
    ("escombreras sin restaurar de fluorita y barita en asturias", ["spain"], [], ["waste dump"], []),
    ("recherche de dépôts de lithium et cobalt en France", ["france"], ["lithium", "cobalt"], [], []),
    ("progetti attivi di rame e cobalto in Italia", ["italy"], ["copper", "cobalt"], [], ["active"]),
    ("unrestored tungsten and tin waste dumps in Germany with water emergence", ["germany"], ["tungsten", "tin"], ["waste dump"], [])
]

for q, co, cm, st, ps in cat5:
    test_cases.append({
        "id": f"TC-{len(test_cases)+1:03d}",
        "category": "noisy_colloquial_multilingual",
        "query": q,
        "expected_intent": "filter_search",
        "expected_filters": {
            "countries": co,
            "commodities": cm,
            "storage_facility_types": st,
            "project_status": ps
        }
    })

assert len(test_cases) == 100, f"Expected 100 cases, got {len(test_cases)}"

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(test_cases, f, indent=2, ensure_ascii=False)

print(f"Successfully created balanced 100-test battery at: {OUTPUT_FILE}")
