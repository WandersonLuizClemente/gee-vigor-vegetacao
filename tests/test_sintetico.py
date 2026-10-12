"""Teste local da análise com dados SINTÉTICOS (sem Earth Engine)."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import config as C, analysis as A

areas = A.carregar_areas()
rng = np.random.default_rng(1)
datas = pd.date_range("2019-01-01", "2026-09-01", freq="MS")
chuva = pd.DataFrame({"data": datas})
chuva["chuva_mm"] = 120 + 90*np.sin((datas.month-11)/12*2*np.pi) + rng.normal(0, 40, len(datas))
chuva["chuva_mm"] = chuva.chuva_mm.clip(lower=0)
zc = (chuva.chuva_mm-chuva.chuva_mm.mean())/chuva.chuva_mm.std()
rows = []
for _, a in areas.iterrows():
    k = {"Pasto": .8, "Milho (pivô)": .1}.get(a.cultura, .35)
    for d, z in zip(datas, zc):
        ndvi = .7 + .08*np.sin((d.month-3)/12*2*np.pi) + k*.04*z + rng.normal(0, .02)
        rows.append({"id": a.id, "cultura": a.cultura, "data": d, "NDVI": ndvi})
df = pd.DataFrame(rows)
sc = A.serie_cultura(df, areas)
ac = A.anomalia_cultura(sc)
sens = A.sensibilidade_hidrica(ac, chuva)
print(sens); print(A.amplitude_sazonal(A.climatologia(sc))); print(A.area_nominal_vs_mapeada(areas))
an = A.anomalias(df); print(an.z.describe()[["count","mean"]])
import os; os.makedirs("/tmp/test_out", exist_ok=True)
A.fig_curvas(sc, destino="/tmp/test_out/curvas.png")
A.fig_anomalias(ac, destino="/tmp/test_out/anom.png")
A.fig_sensibilidade(sens, destino="/tmp/test_out/sens.png")
ult = df[df.data==df.data.max()].set_index("id").NDVI.to_dict()
A.fig_mapa_esquematico(C.GEOJSON_ANON, ult, "NDVI (dado sintético)", destino="/tmp/test_out/mapa.png")
print("OK")
