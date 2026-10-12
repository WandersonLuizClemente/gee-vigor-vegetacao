"""Converte o KML da fazenda em data/talhoes_privado.geojson (uso: python kml_to_geojson.py arquivo.kml)."""
import sys, json
import xml.etree.ElementTree as ET
from config import GEOJSON_PRIVADO

K = "{http://www.opengis.net/kml/2.2}"

def converter(kml, destino=GEOJSON_PRIVADO):
    feats = []
    for fo in ET.parse(kml).getroot().iter(K + "Folder"):
        pasta = fo.find(K + "name").text
        for pm in fo.findall(K + "Placemark"):
            co = pm.find(".//" + K + "Polygon//" + K + "coordinates")
            if co is None:
                continue
            c = [list(map(float, p.split(",")))[:2] for p in co.text.split()]
            feats.append({"type": "Feature",
                          "properties": {"cultura": pasta, "nome": pm.find(K + "name").text.strip()},
                          "geometry": {"type": "Polygon", "coordinates": [c]}})
    json.dump({"type": "FeatureCollection", "features": feats}, open(destino, "w", encoding="utf-8"))
    print(len(feats), "polígonos ->", destino)

if __name__ == "__main__":
    converter(sys.argv[1])
