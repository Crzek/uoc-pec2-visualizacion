"""Prepara los datos de las tres visualizaciones de la PEC 2.

Fuentes (descargadas el 31/10/2026):
- Eurostat nrg_bal_peh (GEP, GWh) y nrg_bal_c (FC_*, KTOE), España, año 2024.
- Bicing: API pública CityBikes (espejo del feed GBFS oficial de Bicing / BSM).
- Banco Mundial: SP.DYN.LE00.IN (esperanza de vida al nacer), 2023.
- Límites de distritos: Ajuntament de Barcelona / CartoBCN (CC-BY), vía github.com/martgnz/bcn-geodata.

Uso: python3 scripts/preparar_datos.py <ruta_districtes.geojson>
"""
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Point, Polygon, shape, mapping
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- SANKEY
KTOE_TO_TWH = 0.01163
GWH_TO_TWH = 0.001

# Generación bruta de electricidad 2024 (GWh) - Eurostat nrg_bal_peh, GEP
gep = {
    "TOTAL": 287914.8, "N900H": 54532.4, "G3000": 52329.1, "C0000X0350-0370": 2581.5,
    "O4000XBIO": 9123.6, "RA100": 34414.7, "RA300": 62089.8, "RA410": 4540.0,
    "RA420": 53752.4, "R5110-5150_W6000RI": 4206.8, "R5300": 1107.5, "W6100_6220": 840.3,
}
fuentes_elec = {
    "Eólica": gep["RA300"],
    "Solar": gep["RA420"] + gep["RA410"],
    "Nuclear": gep["N900H"],
    "Gas natural": gep["G3000"],
    "Hidráulica": gep["RA100"],
    "Petróleo (islas)": gep["O4000XBIO"],
    "Biomasa, biogás y residuos": gep["R5110-5150_W6000RI"] + gep["R5300"] + gep["W6100_6220"],
    "Carbón": gep["C0000X0350-0370"],
}
fuentes_elec["Otras (bombeo y resto)"] = gep["TOTAL"] - sum(fuentes_elec.values())

# Consumo final de energía 2024 (ktoe) - Eurostat nrg_bal_c
fc = {  # sector -> producto -> ktoe
    "Industria": {"E7000": 5864.3, "O4000XBIO": 2005.2, "G3000": 7939.5, "RA000": 2634.1, "C": 288.9, "W": 289.3, "H": 6.4},
    "Transporte": {"E7000": 403.5, "O4000XBIO": 30373.6, "G3000": 358.3, "RA000": 1734.7, "C": 0, "W": 0, "H": 0},
    "Hogares": {"E7000": 6462.4, "O4000XBIO": 2283.2, "G3000": 2916.2, "RA000": 2187.8, "C": 0, "W": 0, "H": 30.4},
    "Comercio y servicios": {"E7000": 6541.4, "O4000XBIO": 1151.9, "G3000": 2139.2, "RA000": 1218.0, "C": 0, "W": 19.8, "H": 11.5},
    "Agricultura, pesca y otros": {
        "E7000": 454.6 + 12.9 + 34.4, "O4000XBIO": 1802.1 + 260.5 + 51.2, "G3000": 88.8 + 15 + 2.6,
        "RA000": 83.6 + 0.1 + 6.4, "C": 39.2, "W": 0, "H": 0},
}
vectores = {
    "E7000": "Electricidad",
    "O4000XBIO": "Petróleo y derivados",
    "G3000": "Gas natural (uso directo)",
    "RA000": "Renovables directas y biocarburantes",
    "C+W+H": "Carbón, residuos y calor",
}

nodes, links = [], []
def node(name, col, grupo):
    nodes.append({"name": name, "col": col, "grupo": grupo})
    return len(nodes) - 1

idx_fuente = {k: node(k, 0, "fuente") for k in fuentes_elec}
idx_vector = {k: node(v, 1, "vector") for k, v in vectores.items()}
idx_sector = {k: node(k, 2, "sector") for k in fc}
idx_perd = node("Pérdidas, autoconsumo y exportación neta", 2, "perdidas")

for k, gwh in fuentes_elec.items():
    links.append({"source": idx_fuente[k], "target": idx_vector["E7000"], "value": round(gwh * GWH_TO_TWH, 2)})
elec_fc = 0
for s, prods in fc.items():
    for code in ["E7000", "O4000XBIO", "G3000", "RA000"]:
        v = prods[code] * KTOE_TO_TWH
        if code == "E7000":
            elec_fc += v
        if v > 0.05:
            links.append({"source": idx_vector[code], "target": idx_sector[s], "value": round(v, 2)})
    otros = (prods["C"] + prods["W"] + prods["H"]) * KTOE_TO_TWH
    if otros > 0.05:
        links.append({"source": idx_vector["C+W+H"], "target": idx_sector[s], "value": round(otros, 2)})
perdidas = gep["TOTAL"] * GWH_TO_TWH - elec_fc
links.append({"source": idx_vector["E7000"], "target": idx_perd, "value": round(perdidas, 2)})

sankey = {
    "titulo": "Flujos de energía en España, 2024 (TWh)",
    "fuente": "Eurostat: nrg_bal_peh (generación bruta de electricidad) y nrg_bal_c (consumo final). Conversión 1 ktoe = 11,63 GWh.",
    "nodes": nodes, "links": links,
}
(ROOT / "sankey" / "flujos_energia_espana_2024.json").write_text(json.dumps(sankey, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"Sankey: {len(nodes)} nodos, {len(links)} enlaces; electricidad generada {gep['TOTAL']/1000:.1f} TWh, "
      f"consumo final eléctrico {elec_fc:.1f} TWh, pérdidas/export {perdidas:.1f} TWh")

# ---------------------------------------------------------------- VORONOI
dist_path = Path(sys.argv[1])
dist = json.loads(dist_path.read_text(encoding="utf-8"))
feats, polys = [], []
for f in dist["features"]:
    g = shape(f["geometry"]).simplify(0.00006, preserve_topology=True)
    polys.append((f["properties"]["NOM"], g))
    gm = mapping(g)
    def rnd(c):
        return [round(c[0], 5), round(c[1], 5)]
    if gm["type"] == "Polygon":
        coords = [[rnd(c) for c in ring] for ring in gm["coordinates"]]
    else:
        coords = [[[rnd(c) for c in ring] for ring in poly] for poly in gm["coordinates"]]
    feats.append({"type": "Feature", "properties": {"nom": f["properties"]["NOM"]},
                  "geometry": {"type": gm["type"], "coordinates": coords}})
(ROOT / "voronoi" / "districtes_bcn.geojson").write_text(
    json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
ciudad = unary_union([p for _, p in polys])

LAT0 = 41.39
KX = 111320 * math.cos(math.radians(LAT0))
KY = 110540
def proj(lon, lat):
    return (lon * KX, lat * KY)

rows, seen_ids = [], {}
with open(ROOT / "voronoi" / "estaciones_raw.csv", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        cap = int(r["capacidad"])
        if cap == 0:  # sin anclajes operativos en el momento de la descarga
            continue
        sid = r["id"]
        seen_ids[sid] = seen_ids.get(sid, 0) + 1
        if seen_ids[sid] > 1:
            sid = f"{sid}-{seen_ids[sid]}"
        lat, lon = float(r["lat"]), float(r["lon"])
        d = next((n for n, p in polys if p.contains(Point(lon, lat))), None)
        rows.append({"id": sid, "nombre": " ".join(r["nombre"].split()).title(), "lat": lat, "lon": lon,
                     "capacidad": cap, "distrito": d or "Fuera de límite"})

# Voronoi en coordenadas proyectadas (m), recortado al término municipal
pts = np.array([proj(r["lon"], r["lat"]) for r in rows])
minx, miny, maxx, maxy = ciudad.bounds
far = [proj(minx - 1, miny - 1), proj(minx - 1, maxy + 1), proj(maxx + 1, miny - 1), proj(maxx + 1, maxy + 1)]
vor = Voronoi(np.vstack([pts, far]))
ciudad_m = Polygon([proj(x, y) for x, y in ciudad.exterior.coords]) if ciudad.geom_type == "Polygon" else \
    unary_union([Polygon([proj(x, y) for x, y in g.exterior.coords]) for g in ciudad.geoms])
for i, r in enumerate(rows):
    reg = vor.regions[vor.point_region[i]]
    cell = Polygon([vor.vertices[j] for j in reg]).intersection(ciudad_m)
    r["area_km2"] = round(cell.area / 1e6, 4)

with open(ROOT / "voronoi" / "estaciones_bicing.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["id", "nombre", "distrito", "lat", "lon", "capacidad", "area_km2"])
    w.writeheader()
    w.writerows(rows)
areas = sorted(r["area_km2"] for r in rows)
print(f"Voronoi: {len(rows)} estaciones; área ciudad {ciudad_m.area/1e6:.1f} km2; "
      f"mediana celda {areas[len(areas)//2]:.3f} km2; máx {areas[-1]:.2f} km2")
by_d = {}
for r in rows:
    by_d.setdefault(r["distrito"], []).append(r["area_km2"])
for d, a in sorted(by_d.items(), key=lambda x: np.median(x[1])):
    print(f"  {d:22s} n={len(a):3d} mediana={np.median(a):.3f} km2")
