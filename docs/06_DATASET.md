# Dataset — "Panamá · Señales y Evidencias v1" (snapshot del equipo)

> Origen, licencia, casos, etiquetado

Fecha de corte: **2026-10-06 21:24 UTC** (`data/raw/manifest.json`). Los SHA-256 del manifest coinciden con los archivos versionados (verificado contra el commit).

## Catálogo

| Archivo | Fuente y URL | Cobertura | Registros | Licencia / condiciones | SHA-256 (inicio) |
|---|---|---|---|---|---|
| `noticias.csv` (TVN) | RSS de TVN, https://www.tvn-2.com/rss/ (ref. [2] del PDF) | Lo que el RSS publicaba al corte; incluye notas desde 2024-09-20 | 152 | Solo título, URL y fecha. El RSS no implica licencia sobre artículos, imágenes o videos | e9be11f8… (archivo completo) |
| `noticias.csv` (GDELT) | GDELT DOC 2.0 ArtList, `api.gdeltproject.org/api/v2/doc/doc` | Detección 2026-09-06 a 2026-10-01; 7 consultas × 6 ventanas de 5 días | 723 | Metadatos; GDELT no transfiere derechos de los medios enlazados | (mismo archivo) |
| `indicadores.csv` | Banco Mundial Indicators API v2 | PAN, CRI, COL, DOM, MEX, GTM × 6 indicadores × 2010–2024 | 540 celdas (0 nulas) | CC BY 4.0, con atribución | d691edc9… |
| `eventos.geojson` | USGS FDSN Event, `earthquake.usgs.gov/fdsnws/event/1/query` | 2024-01-01 a 2024-12-31, lat 5–12, lon −86 a −76, M ≥ 3 | 82 (M máx. 5,8) | Dominio público USGS; citar id y URL | 5909b69c… |
| `casos_controlados.csv` | Sintéticos del equipo | — | 17 | Marcados `origen=sintetico`, dominios `*.test` | — |

## Calidad (T01) — `data/processed/quality_report.json`

| Medida | Valor |
|---|---|
| Noticias totales / válidas / con error | 875 / 875 / 0 |
| De TVN | 152 (mínimo exigido: 20) |
| Medios distintos | 208 |
| Sin fecha de publicación (GDELT solo da detección) | 723 |
| Celdas Banco Mundial con valor / esperadas | 540 / 540 |
| Sismos con campos faltantes / fuera de la caja | 0 / 0 |

Cobertura incompleta: GDELT devolvió HTTP 429 en 29 de 42 ventanas, listadas en `consultas_fallidas` del manifest. Los últimos 5 días antes del corte vienen sobre todo del RSS de TVN.

## Diccionario

**noticias.csv:** `id_noticia` (T/G + SHA-1 de la URL, estable), `titulo`, `url`, `medio` (dominio), `idioma`, `fecha_publicacion` (ISO 8601 UTC; vacía en GDELT), `fecha_deteccion` (seendate de GDELT), `fecha_extraccion`, `tema` (vacío en crudo; lo asigna el agente), `origen` (`tvn_rss` | `gdelt`), `alcance_texto` (`titular/metadatos`).

**indicadores.csv:** `pais_iso3`, `indicador_id`, `anio`, `valor` (vacío = nulo, nunca 0), `unidad`, `fuente_url`, `fecha_extraccion`, `licencia`.

**eventos.geojson:** features USGS con `id`, `mag`, `time`, `updated`, `place`, `status`, `url` y coordenadas (lon, lat, profundidad).

**fichas.jsonl:** `id_caso`, `modalidad`, `ids_fuente`, `afirmaciones`, `citas`, `puntaje`, `componentes`, `estado_evidencia`, `borrador`, `estado_revision` (+ tema, fuentes independientes, sintético, versión de reglas).

## Transformaciones

1. Cuadrícula país × indicador × año completa; los faltantes quedan vacíos.
2. Deduplicación por URL.
3. Unidades del Banco Mundial asignadas por tabla fija por indicador.
4. TVN: solo título, URL y pubDate.
5. GDELT: `fecha_publicacion` vacía y seendate → `fecha_deteccion`.
6. En `processed/` se corrige el espaciado de GDELT ("1 , 500" → "1,500"); `raw/` queda intacto.

## Desviaciones del PDF

- **Intervalo:** el PDF pide los últimos 30 días y a la vez excluir lo que esté fuera de [2024-01-01, 2025-10-01). Con extracción en octubre 2026 son incompatibles; se usó la ventana reciente (D03).
- **1.350 celdas:** 6 × 6 × 15 = 540 (D04).

## Casos sintéticos

| ID | Prueba |
|---|---|
| S-INY-001 | T07: titular que ordena ignorar instrucciones y revelar la clave |
| S-CON-001…010 | T05: cinco pares con cifras incompatibles |
| S-REC-001 | T03: publicada en 2023, detectada en 2026 |
| S-DUP-001…003 | T02: misma nota de EFE en tres medios |

## Etiquetado

| Archivo | Contenido | Método |
|---|---|---|
| `eval/benchmark.jsonl` | 60 consultas: 30 sustentadas, 10 contradicción, 10 sin respuesta, 10 adversariales; 40 dev / 20 reservadas | Propuestas por Claude; PENDIENTE revisión humana |
| `eval/etiquetas_temas.csv` | 150 titulares aleatorios (75 TVN + 75 GDELT, semilla 2026); 100 dev / 50 test | Propuestas por Claude leyendo solo el titular; PENDIENTE revisión |
| `eval/etiquetas_pares.csv` | 60 pares por franjas de similitud (alta, media, baja) | Propuestas por Claude; PENDIENTE revisión |
