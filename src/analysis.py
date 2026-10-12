"""Análise e figuras (pandas + matplotlib). Não depende do Earth Engine."""
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly
from matplotlib.collections import PatchCollection

import config as C

# Paleta categórica validada (ordem fixa, uma cor por cultura)
COR = {"Cacau": "#2a78d6", "Café": "#eb6834", "Banana": "#1baf7a", "Coco": "#eda100",
       "Milho (pivô)": "#e87ba4", "Eucalipto": "#008300", "Pasto": "#4a3aa7", "IPF": "#e34948"}
TXT, TXT2, GRADE = "#0b0b0b", "#52514e", "#e4e3df"
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def _estilo():
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRADE, "axes.labelcolor": TXT2,
                         "xtick.color": TXT2, "ytick.color": TXT2, "text.color": TXT,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.color": GRADE, "grid.linewidth": .6,
                         "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb"})


def carregar_areas(anon=C.GEOJSON_ANON):
    gj = json.load(open(anon, encoding="utf-8"))
    return pd.DataFrame([f["properties"] for f in gj["features"]])


def anomalias(df, var="NDVI"):
    """Anomalia e z-score mensal vs climatologia (período-base) por talhão."""
    d = df[["id", "cultura", "data", var]].dropna().copy()
    d["mes"], d["ano"] = d.data.dt.month, d.data.dt.year
    base = d[(d.ano >= C.BASE_INICIO) & (d.ano <= C.BASE_FIM)]
    cl = base.groupby(["id", "mes"])[var].agg(["mean", "std"]).reset_index()
    d = d.merge(cl, on=["id", "mes"], how="left")
    d["anom"] = d[var] - d["mean"]
    d["z"] = d["anom"] / d["std"].replace(0, np.nan)
    return d



# Culturas dominadas por ciclo de corte/rebrota: fora das anomalias climáticas
CULTURAS_MANEJO = ("Eucalipto", "IPF")


def filtrar_espurios(df, limite=0.12, grupo="id", cols=("NDVI", "NDRE", "NDMI")):
    """Remove quedas de UM mês cercadas por meses normais (nuvem/névoa residual).

    Um mês é espúrio se o NDVI fica `limite` abaixo da média dos vizinhos E
    cada vizinho é mais alto que ele. Quedas sustentadas (corte, seca) não são
    removidas. Use grupo="id" nos talhões e grupo="cultura" na série por cultura.
    Retorna (df_limpo, tabela_dos_removidos).
    """
    d = df.sort_values([grupo, "data"]).copy()
    prev = d.groupby(grupo)["NDVI"].shift(1)
    nxt = d.groupby(grupo)["NDVI"].shift(-1)
    ref = (prev + nxt) / 2
    ruim = ((ref - d["NDVI"]) > limite) & ((prev - d["NDVI"]) > limite / 2) & ((nxt - d["NDVI"]) > limite / 2)
    rem = d.loc[ruim, [grupo, "data", "NDVI"]].copy()
    for c in cols:
        if c in d:
            d.loc[ruim, c] = np.nan
    return d, rem


def filtrar_eventos_sincronos(sc, min_culturas=3, prof=0.06, excluir=CULTURAS_MANEJO):
    """Descarta meses em que várias culturas independentes caem juntas e se recuperam.

    Culturas com fenologias diferentes não caem todas no mesmo mês: é nuvem/névoa/
    atmosfera, não vegetação. Retorna (sc_limpo, lista_de_meses_descartados).
    """
    d = sc.sort_values(["cultura", "data"]).copy()
    g = d.groupby("cultura")["NDVI"]
    prev, nxt = g.shift(1), g.shift(-1)
    fundo = (prev + nxt) / 2 - d["NDVI"]
    spike = (fundo > prof) & (prev - d["NDVI"] > 0.03) & (nxt - d["NDVI"] > 0.03) & (~d["cultura"].isin(excluir))
    cont = d[spike].groupby("data").size()
    meses = list(cont[cont >= min_culturas].index)
    d.loc[d["data"].isin(meses), "NDVI"] = np.nan
    return d, meses


def serie_cultura(df, areas, var="NDVI"):
    """Média ponderada pela área, por cultura e mês."""
    d = df.merge(areas[["id", "area_ha"]], on="id")
    d = d.dropna(subset=[var])
    g = d.groupby(["cultura", "data"]).apply(
        lambda x: np.average(x[var], weights=x.area_ha), include_groups=False)
    return g.rename(var).reset_index()


def climatologia(sc, var="NDVI"):
    d = sc.copy(); d["mes"] = d.data.dt.month; d["ano"] = d.data.dt.year
    d = d[(d.ano >= C.BASE_INICIO) & (d.ano <= C.BASE_FIM)]
    return d.groupby(["cultura", "mes"])[var].mean().unstack("mes")


def anomalia_cultura(sc, var="NDVI"):
    d = sc.copy(); d["mes"] = d.data.dt.month; d["ano"] = d.data.dt.year
    base = d[(d.ano >= C.BASE_INICIO) & (d.ano <= C.BASE_FIM)]
    cl = base.groupby(["cultura", "mes"])[var].agg(["mean", "std"]).reset_index()
    d = d.merge(cl, on=["cultura", "mes"])
    d["z"] = (d[var] - d["mean"]) / d["std"].replace(0, np.nan)
    return d


def _z_chuva(clima):
    c = clima.copy(); c["mes"] = c.data.dt.month; c["ano"] = c.data.dt.year
    b = c[(c.ano >= C.BASE_INICIO) & (c.ano <= C.BASE_FIM)].groupby("mes").chuva_mm.agg(["mean", "std"])
    c = c.join(b, on="mes")
    c["z_chuva"] = (c.chuva_mm - c["mean"]) / c["std"].replace(0, np.nan)
    return c[["data", "chuva_mm", "z_chuva"]]


def sensibilidade_hidrica(anom_cult, clima, lags=(0, 1, 2, 3)):
    """Correlação (Pearson) entre z do NDVI e z da chuva defasada, por cultura."""
    z = _z_chuva(clima).set_index("data").z_chuva
    linhas = []
    for cult, g in anom_cult.groupby("cultura"):
        s = g.set_index("data").z.dropna()
        melhor = None
        for L in lags:
            zz = z.shift(L).reindex(s.index)
            ok = s.notna() & zz.notna()
            if ok.sum() < 24:
                continue
            r = np.corrcoef(s[ok], zz[ok])[0, 1]
            if melhor is None or abs(r) > abs(melhor[1]):
                melhor = (L, r, int(ok.sum()))
        if melhor:
            linhas.append({"cultura": cult, "lag_meses": melhor[0], "r": round(melhor[1], 2), "n": melhor[2]})
    return pd.DataFrame(linhas).sort_values("r", ascending=False).reset_index(drop=True)


def amplitude_sazonal(clim):
    out = pd.DataFrame({"min": clim.min(axis=1), "max": clim.max(axis=1)})
    out["amplitude"] = out["max"] - out["min"]
    out["mes_pico"] = [MESES[int(i) - 1] for i in clim.idxmax(axis=1)]
    return out.round(3).sort_values("amplitude", ascending=False)


def area_nominal_vs_mapeada(areas):
    t = areas.dropna(subset=["area_nominal_ha"]).copy()
    t["dif_ha"] = (t.area_ha - t.area_nominal_ha).round(1)
    t["dif_pct"] = (100 * t.dif_ha / t.area_nominal_ha).round(0)
    return t[["id", "cultura", "area_nominal_ha", "area_ha", "dif_ha", "dif_pct"]]


# ---------------------------------------------------------------- figuras
def fig_curvas(sc, var="NDVI", destino=None):
    _estilo()
    culturas = [c for c in COR if c in set(sc.cultura)]
    fig, axs = plt.subplots(2, 4, figsize=(15, 6.2), sharex=True, sharey=True)
    for ax, c in zip(axs.flat, culturas):
        g = sc[sc.cultura == c]
        ax.plot(g.data, g[var], color=COR[c], lw=2)
        ax.set_title(c, loc="left", fontsize=11, fontweight="bold")
    for ax in axs.flat[len(culturas):]:
        ax.axis("off")
    fig.suptitle(f"{var} mensal por cultura (Sentinel-2, média ponderada por área)",
                 x=.01, ha="left", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, .95))
    if destino: fig.savefig(destino, dpi=170)
    return fig


def fig_anomalias(anom_cult, destino=None):
    """Heatmap cultura x mês do z-score do NDVI (divergente, centro neutro)."""
    _estilo()
    p = anom_cult.pivot_table(index="cultura", columns="data", values="z")
    p = p.reindex([c for c in COR if c in p.index])
    fig, ax = plt.subplots(figsize=(15, 3.8))
    im = ax.imshow(p.values, aspect="auto", cmap="RdBu", vmin=-3, vmax=3)
    ax.set_yticks(range(len(p.index))); ax.set_yticklabels(p.index)
    anos = [i for i, d in enumerate(p.columns) if d.month == 1]
    ax.set_xticks(anos); ax.set_xticklabels([p.columns[i].year for i in anos])
    ax.grid(False)
    cb = fig.colorbar(im, ax=ax, pad=.01); cb.set_label("z-score do NDVI (vs. climatologia)")
    ax.set_title("Onde e quando a vegetação fugiu do normal  (azul = acima, vermelho = abaixo)",
                 loc="left", fontsize=12, fontweight="bold")
    fig.tight_layout()
    if destino: fig.savefig(destino, dpi=170)
    return fig


def fig_sensibilidade(sens, destino=None):
    _estilo()
    s = sens.sort_values("r")
    fig, ax = plt.subplots(figsize=(7.5, 4))
    ax.barh(s.cultura, s.r, color=[COR.get(c, "#888") for c in s.cultura], height=.6)
    for y, (r, L) in enumerate(zip(s.r, s.lag_meses)):
        ax.text(max(r, 0) + .01, y, f"{r:+.2f}  (defasagem {L} m)",
                va="center", ha="left", fontsize=9, color=TXT2)
    ax.set_xlabel("correlação NDVI × chuva (z-scores)"); ax.grid(axis="y", visible=False)
    ax.set_xlim(min(-.1, s.r.min() - .02), max(.6, s.r.max() + .2))
    ax.set_title("Qual cultura responde mais à chuva?", loc="left", fontweight="bold")
    ax.axvline(0, color=TXT2, lw=.8)
    fig.tight_layout()
    if destino: fig.savefig(destino, dpi=170)
    return fig


def fig_mapa_esquematico(areas_gj, valores, rotulo, destino=None, cmap="YlGn"):
    """Mapa sem base cartográfica (coordenadas anônimas), colorido por 'valores'[id]."""
    _estilo()
    gj = json.load(open(areas_gj, encoding="utf-8"))
    patches, vals = [], []
    for f in gj["features"]:
        patches.append(MplPoly(np.array(f["geometry"]["coordinates"][0])))
        vals.append(valores.get(f["properties"]["id"], np.nan))
    fig, ax = plt.subplots(figsize=(8, 6.5))
    pc = PatchCollection(patches, cmap=cmap, edgecolor="#fcfcfb", linewidth=1.2)
    pc.set_array(np.array(vals)); ax.add_collection(pc); ax.autoscale_view()
    ax.set_aspect("equal"); ax.axis("off")
    fig.colorbar(pc, ax=ax, shrink=.7, label=rotulo)
    ax.set_title(rotulo, loc="left", fontweight="bold")
    fig.tight_layout()
    if destino: fig.savefig(destino, dpi=170)
    return fig


# Calendário de manejo do café conilon no ES (Incaper/Agrolink, informado pelo autor)
CAFE_CALENDARIO = [  # (mês ini, mês fim, rótulo, cor, x do rótulo, rotação)
    (4, 6, "Colheita (abr–jun)", "#d9d8d3", 4.2, 0),
    (5, 8, "Poda (mai–ago, pico jul)", "#e9c9b8", 7.3, 0),
    (9, 9, "Tratos / adubação", "#cfdcec", 9.0, 90),
]


def fig_cafe_manejo(df, destino=None, ate=2025):
    """NDVI mensal médio do café (climatologia) sobreposto ao calendário de manejo."""
    _estilo()
    d = df[(df.cultura == "Café") & (df.data.dt.year <= ate)].copy()
    d["mes"] = d.data.dt.month
    por_id = d.groupby(["id", "mes"]).NDVI.mean().unstack(0)
    media = por_id.mean(axis=1)
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    for m0, m1, rot, cor, xl, ang in CAFE_CALENDARIO:
        ax.axvspan(m0 - .5, m1 + .5, color=cor, alpha=.55, lw=0)
        ax.text(xl, .775, rot, ha="center", va="top", fontsize=8.5, color=TXT2, rotation=ang)
    for c in por_id:
        ax.plot(por_id.index, por_id[c], color="#b7b6b0", lw=1)
    ax.plot(media.index, media.values, color=COR["Café"], lw=3, label="Café (média dos talhões)")
    ax.set_xticks(range(1, 13)); ax.set_xticklabels(MESES)
    ax.set_xlim(.5, 12.5); ax.set_ylim(.44, .78)
    ax.set_ylabel("NDVI médio (2019–2025)")
    ax.set_title("O NDVI do café acompanha o calendário de colheita e poda",
                 loc="left", fontweight="bold")
    ax.text(12.4, media.loc[12] + .012, "brotação\ne florada", ha="right", fontsize=8.5, color=TXT2)
    fig.tight_layout()
    if destino: fig.savefig(destino, dpi=170)
    return fig
