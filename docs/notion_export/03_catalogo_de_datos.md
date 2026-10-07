# Catálogo de datos

Snapshot "Panamá · Señales y Evidencias v1" del equipo. Corte: **2026-10-06 21:24 UTC** (16:24 hora de Panamá). Detalle completo en `docs/06_DATASET.md` y `data/raw/manifest.json`.

| Fuente | URL | Fecha de extracción | Cobertura | Campos | Licencia / condiciones | Transformaciones | Registros | SHA-256 del snapshot |
|---|---|---|---|---|---|---|---|---|
| TVN · RSS | https://www.tvn-2.com/rss/ | 2026-10-06 21:24 UTC | Lo publicado en el feed al corte (notas desde 2024-09-20 hasta 2026-10-06) | id_noticia, titulo, url, medio, idioma, fecha_publicacion, fecha_extraccion, origen, alcance_texto | Solo metadatos; el RSS no implica licencia sobre textos, imágenes ni videos | Sin descripción ni cuerpo; dedupe por URL | 152 | `noticias.csv`: e9be11f8706eae61834401ee5ff41a929411c2eaeb3b4b76536c8b4e01206eb9 |
| GDELT DOC 2.0 | https://api.gdeltproject.org/api/v2/doc/doc | 2026-10-06 21:24 UTC | Detección 2026-09-06 a 2026-10-01; 7 consultas × 6 ventanas de 5 días; 29 ventanas fallaron (HTTP 429) | id_noticia, titulo, url, medio, idioma, fecha_deteccion (seendate), fecha_extraccion | Metadatos; no transfiere derechos de los medios enlazados | fecha_publicacion vacía; espaciado normalizado solo en `processed/`; dedupe por URL | 723 | (mismo archivo `noticias.csv`) |
| Banco Mundial · Indicators API v2 | https://api.worldbank.org/v2/ | 2026-10-06 21:24 UTC | PAN, CRI, COL, DOM, MEX, GTM × NY.GDP.MKTP.KD.ZG, FP.CPI.TOTL.ZG, SL.UEM.TOTL.ZS, SP.POP.TOTL, IT.NET.USER.ZS, NE.EXP.GNFS.ZS × 2010–2024 | pais_iso3, indicador_id, anio, valor (nullable), unidad, fuente_url, fecha_extraccion, licencia | CC BY 4.0 con atribución | Cuadrícula completa con nulos explícitos (0 nulos al corte); unidad por tabla fija | 540 | `indicadores.csv`: d691edc9cbdc083e6c441d2f62c449a8f7c3c3c11cda92d792faf334fa019494 |
| USGS · FDSN Event | https://earthquake.usgs.gov/fdsnws/event/1/query | 2026-10-06 21:24 UTC | 2024-01-01 a 2024-12-31; lat 5–12, lon −86 a −76; M ≥ 3 | id, magnitude, time, updated, longitude, latitude, depth, place, status, url | Dominio público USGS; citar id y URL | Ninguna; solo se usa para hechos sísmicos | 82 | `eventos.geojson`: 5909b69c22041ad9ed0ad3188362094f173534a7a45f0cc7b14757aa67d382d5 |
| Casos controlados | `data/synthetic/casos_controlados.csv` | Creados por el equipo | Inyección, 5 pares de contradicciones, recirculada, agencia replicada | Mismo contrato que noticias + `caso` | Sintéticos, dominios `*.test` | Rotulados `origen=sintetico` | 17 | — |

**Desviaciones del PDF.**
- **Intervalo de fechas:** se usó la ventana reciente en lugar de [2024-01-01, 2025-10-01). Ver la decisión D03.
- **Tamaño de la cuadrícula:** son 540 celdas y no 1.350. Ver la decisión D04.
