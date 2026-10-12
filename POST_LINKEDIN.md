# Rascunho do post (números reais; ajuste o tom)

Passei 7 anos de imagens do satélite Sentinel-2 por 23 talhões de 8 usos do solo.
O que o espaço mostrou sobre pasto, café, cacau, banana, coco, milho e eucalipto 🛰️🌱

Usei Google Earth Engine + Python e encontrei 5 coisas:

1️⃣ O satélite viu o corte do eucalipto. O NDVI caiu a ~0,18 em meados de 2024 e voltou a ~0,8 em 2025 (corte e rebrota). Sem ninguém avisar.

2️⃣ O pasto, sem irrigação, é o que mais depende da chuva (r = 0,41, com 1 mês de atraso). Coco e banana, irrigados, quase não reagem.

3️⃣ O pasto é o que mais oscila no ano (NDVI de 0,43 a 0,67); a banana quase não muda (0,78 a 0,86).

4️⃣ O café mostra o manejo: NDVI no pico em maio, queda durante colheita e poda, mínimo em setembro e recuperação com a brotação. O satélite desenha o calendário do Incaper nos 5 talhões.

5️⃣ Áreas nominais não batem com a mapeada: um talhão de "100 ha" tem 146 ha. O satélite também audita o cadastro.

O trabalho de verdade foi a limpeza. Nuvem e névoa criaram quedas falsas de NDVI em vários meses, e tive que removê-las com critério (meses em que várias culturas independentes caem juntas não são vegetação, são atmosfera).

Método: Sentinel-2 + Cloud Score+, composto mensal, z-score contra climatologia 2019–2025. Dados anonimizados.

Código e notebook: [link GitHub]

Trabalho com mapeamento por drone e análise de dados na manutenção e na agricultura. Quer ver essa análise numa outra área?

#GoogleEarthEngine #Sentinel2 #SensoriamentoRemoto #Geoprocessamento #AgriculturaDePrecisão #Python
