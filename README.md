# PEC 2 · Visualización de datos (UOC)

En esta PEC me han asignado tres técnicas de visualización. He aplicado cada una a un conjunto de datos abiertos y las he publicado en GitHub Pages:

| Técnica | Visualización | Datos |
|---|---|---|
| Sankey (Grupo I) | [Flujos de energía en España 2024](https://crzek.github.io/uoc-pec2-visualizacion/sankey/) | Eurostat `nrg_bal_peh` y `nrg_bal_c` |
| Voronoi (Grupo II) | [Área de influencia del Bicing](https://crzek.github.io/uoc-pec2-visualizacion/voronoi/) | Bicing (GBFS vía CityBikes) + límites de distrito CartoBCN |
| Beeswarm (Grupo III) | [Esperanza de vida en el mundo 2023](https://crzek.github.io/uoc-pec2-visualizacion/beeswarm/) | Banco Mundial `SP.DYN.LE00.IN` |

Portada: https://crzek.github.io/uoc-pec2-visualizacion/

## Estructura

- `sankey/`, `voronoi/`, `beeswarm/`: cada página (`index.html`) y sus datos ya preparados.
- `scripts/preparar_datos.py`: el script con el que genero el JSON del Sankey, recorto las celdas de Voronoi al término municipal y calculo su área.
- `lib/`: D3.js v7, d3-sankey y la hoja de estilos compartida (modo claro y oscuro).

He hecho las páginas en HTML estático con D3, así que no hace falta compilar nada.
