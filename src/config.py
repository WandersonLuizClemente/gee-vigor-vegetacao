"""Configuração central do projeto."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"

# Projeto Google Cloud registrado no Earth Engine (troque pelo seu)
EE_PROJECT = "SERIE DE ACOMPANHAMENTO TEMPORAL"   # seu ID do passo 1


# Geometrias reais (privadas, fora do git) e versão anonimizada (publicável)
GEOJSON_PRIVADO = DATA / "talhoes_privado.geojson"
GEOJSON_ANON = DATA / "talhoes_anonimo.geojson"

# Janela de análise
INICIO = "2019-01-01"
FIM = "2026-09-30"
# Período-base para a climatologia (anomalias)
BASE_INICIO, BASE_FIM = 2019, 2025

# Sentinel-2 / Cloud Score+
S2 = "COPERNICUS/S2_SR_HARMONIZED"
CSPLUS = "GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED"
CS_MIN = 0.60          # limiar do cs_cdf (0.60 = bom compromisso)
ESCALA = 10            # metros

# Agrupamentos de culturas para análise (nomes de pasta do KML -> rótulo)
CULTURAS = {
    "CACAU": "Cacau", "CAFÉ": "Café", "BANANA": "Banana", "COCO": "Coco",
    "MILHO": "Milho (pivô)", "EUCALIPTO": "Eucalipto", "PASTO": "Pasto",
    "IPF - INTEGRAÇÃO PECUÁRIA - FLORESTA": "IPF",
}
