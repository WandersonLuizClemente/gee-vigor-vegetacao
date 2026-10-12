"""Anonimiza os talhões para publicação.

- remove nomes originais (ficam só cultura + ID genérico, ex.: Cacau-01)
- converte para coordenadas métricas locais, giradas por um ângulo aleatório
  (seed fixa) e com origem arbitrária -> não há como recuperar a localização
- preserva forma, área e vizinhança relativa dos talhões
- guarda a área "nominal" (número que aparecia no nome, ex.: "100 Ha.")

A análise de satélite roda na geometria REAL (privada). Só os resultados
anonimizados (CSV/figuras/mapa esquemático) vão para o repositório público.
"""
import json
import math
import re
import random
from collections import defaultdict

from config import GEOJSON_PRIVADO, GEOJSON_ANON, CULTURAS

R = 6371008.8


def area_ha(xy):
    a = sum(xy[i][0] * xy[i + 1][1] - xy[i + 1][0] * xy[i][1] for i in range(len(xy) - 1))
    return abs(a) / 2 / 1e4


def nominal_ha(nome):
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*ha", nome, flags=re.I)
    return float(m.group(1).replace(",", ".")) if m else None


def anonimizar(origem=GEOJSON_PRIVADO, destino=GEOJSON_ANON, seed=2026):
    gj = json.load(open(origem, encoding="utf-8"))
    rng = random.Random(seed)
    ang = rng.uniform(0, 2 * math.pi)
    ox, oy = rng.uniform(1e5, 9e5), rng.uniform(1e5, 9e5)  # origem fictícia

    pts = [p for f in gj["features"] for p in f["geometry"]["coordinates"][0]]
    lon0 = sum(p[0] for p in pts) / len(pts)
    lat0 = sum(p[1] for p in pts) / len(pts)
    k = math.cos(math.radians(lat0))

    def proj(p):
        x = math.radians(p[0] - lon0) * R * k
        y = math.radians(p[1] - lat0) * R
        xr = x * math.cos(ang) - y * math.sin(ang)
        yr = x * math.sin(ang) + y * math.cos(ang)
        return [round(xr + ox, 1), round(yr + oy, 1)]

    cont = defaultdict(int)
    feats = []
    for f in gj["features"]:
        cult = CULTURAS.get(f["properties"]["cultura"], f["properties"]["cultura"])
        cont[cult] += 1
        xy = [proj(p) for p in f["geometry"]["coordinates"][0]]
        feats.append({
            "type": "Feature",
            "properties": {
                "id": f"{cult.split()[0]}-{cont[cult]:02d}",
                "cultura": cult,
                "area_ha": round(area_ha(xy), 1),
                "area_nominal_ha": nominal_ha(f["properties"]["nome"]),
            },
            "geometry": {"type": "Polygon", "coordinates": [xy]},
        })
    out = {"type": "FeatureCollection", "crs_nota": "metros locais, sem georreferência",
           "features": feats}
    json.dump(out, open(destino, "w", encoding="utf-8"), ensure_ascii=False)
    return out


def tabela_ids(origem=GEOJSON_PRIVADO, seed=2026):
    """Mapa nome-real -> ID anônimo (guarde fora do git; só para você)."""
    gj = json.load(open(origem, encoding="utf-8"))
    cont = defaultdict(int)
    m = []
    for f in gj["features"]:
        cult = CULTURAS.get(f["properties"]["cultura"], f["properties"]["cultura"])
        cont[cult] += 1
        m.append((f"{cult.split()[0]}-{cont[cult]:02d}", f["properties"]["nome"]))
    return m


if __name__ == "__main__":
    o = anonimizar()
    print(len(o["features"]), "talhões anonimizados ->", GEOJSON_ANON)
