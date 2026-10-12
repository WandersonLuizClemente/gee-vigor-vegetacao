"""Extração no Google Earth Engine: séries mensais por talhão.

Rodar localmente ou no Colab (precisa de autenticação: ee.Authenticate()).
Saída: DataFrame com NDVI/NDRE/NDMI médios por talhão e mês, além de chuva
(CHIRPS) e temperatura de superfície (MODIS LST) para a área da fazenda.
"""
import json
import pandas as pd
import ee

import config as C
from anonymize import tabela_ids


def iniciar(projeto=C.EE_PROJECT):
    try:
        ee.Initialize(project=projeto)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=projeto)


def talhoes_fc():
    """FeatureCollection com as geometrias REAIS e IDs anônimos."""
    gj = json.load(open(C.GEOJSON_PRIVADO, encoding="utf-8"))
    ids = [i for i, _ in tabela_ids()]
    feats = []
    for i, f in zip(ids, gj["features"]):
        cult = C.CULTURAS.get(f["properties"]["cultura"], f["properties"]["cultura"])
        feats.append(ee.Feature(ee.Geometry.Polygon(f["geometry"]["coordinates"]),
                                {"id": i, "cultura": cult}))
    return ee.FeatureCollection(feats)


def _indices(img):
    return img.addBands([
        img.normalizedDifference(["B8", "B4"]).rename("NDVI"),
        img.normalizedDifference(["B8", "B5"]).rename("NDRE"),
        img.normalizedDifference(["B8", "B11"]).rename("NDMI"),
    ])


def _s2_mascarado(aoi, ini, fim):
    s2 = (ee.ImageCollection(C.S2).filterBounds(aoi).filterDate(ini, fim)
          .linkCollection(ee.ImageCollection(C.CSPLUS), ["cs_cdf"]))
    return s2.map(lambda im: _indices(im.updateMask(im.select("cs_cdf").gte(C.CS_MIN)))
                  .select(["NDVI", "NDRE", "NDMI"]))


def composto_mensal(aoi, ano, mes):
    ini = ee.Date.fromYMD(ano, mes, 1)
    return _s2_mascarado(aoi, ini, ini.advance(1, "month")).median()


def serie_s2(fc, anos=None):
    """Médias mensais por talhão (um getInfo por ano, para não estourar limites)."""
    aoi = fc.geometry().bounds()
    anos = anos or range(int(C.INICIO[:4]), int(C.FIM[:4]) + 1)
    red = ee.Reducer.mean()
    linhas = []
    for ano in anos:
        def por_mes(m):
            m = ee.Number(m)
            ini = ee.Date.fromYMD(ano, m, 1)
            col = _s2_mascarado(aoi, ini, ini.advance(1, "month"))
            comp = col.median()
            out = comp.reduceRegions(fc, red, C.ESCALA, tileScale=4)
            out = out.map(lambda f: f.set({"ano": ano, "mes": m, "n_cenas": col.size()})
                          .setGeometry(None))
            return ee.Algorithms.If(col.size().gt(0), out, ee.FeatureCollection([]))
        ano_fc = ee.FeatureCollection(ee.List.sequence(1, 12).map(por_mes)).flatten()
        linhas += [f["properties"] for f in ano_fc.getInfo()["features"]]
        print("S2", ano, "ok")
    df = pd.DataFrame(linhas)
    df["data"] = pd.to_datetime(dict(year=df.ano, month=df.mes, day=1))
    df = df[df.data <= pd.to_datetime(C.FIM)]      # nada além da data final (mês incompleto)
    return df.sort_values(["id", "data"]).reset_index(drop=True)


def clima_mensal(fc):
    """Chuva (CHIRPS, mm/mês) e LST diurna (MODIS, °C) médias sobre a fazenda.

    Meses sem dado (CHIRPS/MODIS publicam com atraso) viram NaN.
    """
    aoi = fc.geometry().bounds()
    a0, a1 = int(C.INICIO[:4]), int(C.FIM[:4])
    meses = ee.List([ee.Date.fromYMD(a, m, 1) for a in range(a0, a1 + 1) for m in range(1, 13)])
    chirps = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").select("precipitation")
    lst = ee.ImageCollection("MODIS/061/MOD11A2").select("LST_Day_1km")
    SEM = -9999

    def f(d):
        d = ee.Date(d)
        fim = d.advance(1, "month")
        col_c = chirps.filterDate(d, fim)
        col_t = lst.filterDate(d, fim)
        chuva = ee.Algorithms.If(
            col_c.size().gt(0),
            ee.Dictionary(col_c.sum().reduceRegion(ee.Reducer.mean(), aoi, 5000)).get("precipitation", SEM),
            SEM)
        t = ee.Algorithms.If(
            col_t.size().gt(0),
            ee.Dictionary(col_t.mean().multiply(0.02).subtract(273.15)
                          .reduceRegion(ee.Reducer.mean(), aoi, 1000)).get("LST_Day_1km", SEM),
            SEM)
        return ee.Feature(None, {"data": d.format("YYYY-MM-dd"), "chuva_mm": chuva, "lst_c": t})

    out = ee.FeatureCollection(meses.map(f)).getInfo()["features"]
    df = pd.DataFrame([o["properties"] for o in out])
    df["data"] = pd.to_datetime(df["data"])
    df = df.replace(SEM, float("nan"))
    return df[df.data <= pd.to_datetime(C.FIM)].reset_index(drop=True)
