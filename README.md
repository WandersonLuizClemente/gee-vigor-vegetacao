# 🌱 Vigor da vegetação por cultura — Sentinel-2 + Google Earth Engine

Série mensal 2019–2026 de **NDVI, NDRE e NDMI** em 23 talhões de 8 usos do solo
(cacau, café, banana, coco, milho irrigado, eucalipto, pasto e integração pecuária-floresta),
cruzada com chuva (CHIRPS) e temperatura de superfície (MODIS).

**Perguntas respondidas**
1. Qual o perfil sazonal de cada cultura?
2. Quando a vegetação saiu do normal (anomalias vs. climatologia)?
3. Qual cultura responde mais à chuva, e com quantos meses de defasagem?
4. A área nominal dos talhões bate com a área mapeada?

## Método
- **Sentinel-2 SR Harmonizado** + máscara **Cloud Score+** (`cs_cdf ≥ 0,60`)
- Composto mensal por mediana → média por talhão (10 m)
- Índices: NDVI (B8,B4), NDRE (B8,B5), NDMI (B8,B11)
- Anomalia = z-score contra a climatologia 2019–2025, por talhão e mês
- Sensibilidade hídrica = correlação de Pearson entre z(NDVI) e z(chuva), defasagem 0–3 meses
- Agregação por cultura ponderada pela área

## Resultados
_(preencher após rodar: `outputs/01_curvas_ndvi.png`, `02_anomalias.png`, `03_sensibilidade_chuva.png`, `04_mapa_ndvi.png`)_

## Privacidade
Os dados reais ficam fora do git (`.gitignore`). A análise roda na geometria real; o
repositório publica apenas resultados com **IDs anônimos** e um mapa esquemático em
coordenadas locais rotacionadas (sem base cartográfica).

## Como rodar
```bash
pip install -r requirements.txt
earthengine authenticate            # projeto GCP com Earth Engine habilitado
# 1. python src/kml_to_geojson.py SEU_ARQUIVO.kml   (gera data/talhoes_privado.geojson)
# 2. edite EE_PROJECT em src/config.py
jupyter lab notebooks/analise_gee.ipynb
python tests/test_sintetico.py      # testa a análise sem Earth Engine (dados sintéticos)
```

## Limitações
Média por polígono inclui estradas e bordas; NDVI satura em dossel denso (use NDRE);
sem validação de campo; CHIRPS tem resolução de ~5 km.

---
## English summary
Monthly Sentinel-2 (Cloud Score+ masked) NDVI/NDRE/NDMI time series for 23 plots across 8
tropical land uses in Brazil (2019–2026), analysed for seasonality, anomalies and rainfall
sensitivity (lagged correlation with CHIRPS). Geometries are anonymised for publication.
Built with Python, `earthengine-api`, `geemap`, pandas and matplotlib.
