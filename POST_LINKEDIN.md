# Rascunho do post (ajuste com os seus números reais depois de rodar)

Passei 7 anos de imagens Sentinel-2 por 23 talhões de 8 culturas diferentes.
O que o satélite mostrou sobre cacau, café, banana, coco, milho, eucalipto e pasto 🛰️🌱

Usei Google Earth Engine + Python para responder 3 perguntas:
1️⃣ Como cada cultura se comporta ao longo do ano?
2️⃣ Quando a vegetação fugiu do normal?
3️⃣ Qual cultura responde mais à chuva — e com quantos meses de atraso?

O que encontrei:
• [cultura X] tem a maior amplitude sazonal (NDVI de __ a __)
• [mês/ano] foi o pior período de anomalia: [culturas] ficaram __σ abaixo do normal
• [cultura Y] respondeu mais à chuva (r = __, defasagem de __ meses)
• As áreas nominais dos talhões diferiam da área mapeada em até __% — o satélite também audita o cadastro

Método: Sentinel-2 + Cloud Score+, composto mensal, z-score contra climatologia 2019–2025.
Dados anonimizados.

Código e notebook: [link GitHub]

Trabalho com mapeamento por drone e análise de dados na manutenção e na agricultura.
Quer ver esse tipo de análise em outra área? Me chama.

#GoogleEarthEngine #Sentinel2 #SensoriamentoRemoto #Geoprocessamento #AgriculturaDePrecisão #Python
