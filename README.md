# PEC 2 · Visualización de datos (UOC)

Tres técnicas de visualización asignadas, cada una con datos abiertos y publicada en GitHub Pages:

| Técnica | Visualización | Datos |
|---|---|---|
| Sankey (Grupo I) | [Flujos de energía en España 2024](https://crzek.github.io/uoc-pec2-visualizacion/sankey/) | Eurostat `nrg_bal_peh` y `nrg_bal_c` |
| Voronoi (Grupo II) | [Área de influencia del Bicing](https://crzek.github.io/uoc-pec2-visualizacion/voronoi/) | Bicing (GBFS vía CityBikes) + límites de distrito CartoBCN |
| Beeswarm (Grupo III) | [Esperanza de vida en el mundo 2023](https://crzek.github.io/uoc-pec2-visualizacion/beeswarm/) | Banco Mundial `SP.DYN.LE00.IN` |

Portada: https://crzek.github.io/uoc-pec2-visualizacion/

## Estructura

- `sankey/`, `voronoi/`, `beeswarm/`: cada página (`index.html`) y sus datos ya preparados.
- `scripts/preparar_datos.py`: genera el JSON del Sankey, recorta las celdas de Voronoi al término municipal y calcula su área.
- `lib/`: D3.js v7, d3-sankey y la hoja de estilos compartida (modo claro y oscuro).

Las páginas son HTML estático con D3. No hace falta compilar nada.
