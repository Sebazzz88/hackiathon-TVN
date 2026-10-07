# Catálogo de datos (generado)

Generado desde `data/raw/manifest.json` (versión `v1`). Corte del snapshot: **2026-10-06 16:24 (Panamá)** (2026-10-06T21:24:22+00:00 UTC).

| Archivo | Registros | SHA-256 |
|---|---|---|
| `eventos.geojson` | 82 | `5909b69c22041ad9ed0ad3188362094f173534a7a45f0cc7b14757aa67d382d5` |
| `indicadores.csv` | 540 | `d691edc9cbdc083e6c441d2f62c449a8f7c3c3c11cda92d792faf334fa019494` |
| `noticias.csv` | 875 | `e9be11f8706eae61834401ee5ff41a929411c2eaeb3b4b76536c8b4e01206eb9` |

**Licencias y condiciones:** Banco Mundial CC BY 4.0; USGS y GDELT: revisar condiciones; TVN: solo metadatos, sin republicar contenido

**Ventana de noticias:** 30 días. El PDF propone [2024-01-01, 2025-10-01) pero también 'últimos 30 días'; GDELT DOC solo cubre ~3 meses. Se usa la ventana reciente (ver docs/09_DECISIONS.md).

**Transformaciones:**

- Cuadrícula país×indicador×año completa con nulos explícitos
- Dedupe por URL
- Unidades de indicadores asignadas por tabla fija
- TVN: solo título/URL/pubDate (sin descripción)
- GDELT: fecha_publicacion vacía; seendate -> fecha_deteccion

**Consultas ejecutadas:** 50 · **fallidas:** 29. GDELT devolvió HTTP 429 (límite de tasa) en varias ventanas; esas consultas quedaron sin datos y se listan en consultas_fallidas. Cobertura efectiva GDELT por fecha de detección: ver data/processed/quality_report.json.

<details><summary>Consultas fallidas</summary>

- Panama ventana 20-25 días antes del corte (HTTP 429)
- Panama logistica ventana 0-5 días antes del corte (HTTP 429)
- Panama logistica ventana 5-10 días antes del corte (HTTP 429)
- Panama logistica ventana 15-20 días antes del corte (HTTP 429)
- Panama logistica ventana 20-25 días antes del corte (HTTP 429)
- Panama logistica ventana 25-30 días antes del corte (HTTP 429)
- Panama canal ventana 0-5 días antes del corte (HTTP 429)
- Panama canal ventana 5-10 días antes del corte (HTTP 429)
- Panama canal ventana 20-25 días antes del corte (HTTP 429)
- Panama canal ventana 25-30 días antes del corte (HTTP 429)
- Panama turismo ventana 5-10 días antes del corte (HTTP 429)
- Panama turismo ventana 10-15 días antes del corte (HTTP 429)
- Panama turismo ventana 15-20 días antes del corte (HTTP 429)
- Panama economia ventana 0-5 días antes del corte (HTTP 429)
- Panama economia ventana 10-15 días antes del corte (HTTP 429)
- Panama economia ventana 15-20 días antes del corte (HTTP 429)
- Panama economia ventana 20-25 días antes del corte (HTTP 429)
- Panama economia ventana 25-30 días antes del corte (HTTP 429)
- Panama sismo ventana 0-5 días antes del corte (HTTP 429)
- Panama sismo ventana 5-10 días antes del corte (HTTP 429)
- Panama sismo ventana 10-15 días antes del corte (HTTP 429)
- Panama sismo ventana 15-20 días antes del corte (HTTP 429)
- Panama sismo ventana 20-25 días antes del corte (HTTP 429)
- Panama sismo ventana 25-30 días antes del corte (HTTP 429)
- sourcecountry:panama ventana 0-5 días antes del corte (HTTP 429)
- sourcecountry:panama ventana 10-15 días antes del corte (HTTP 429)
- sourcecountry:panama ventana 15-20 días antes del corte (HTTP 429)
- sourcecountry:panama ventana 20-25 días antes del corte (HTTP 429)
- sourcecountry:panama ventana 25-30 días antes del corte (HTTP 429)

</details>

**Consultas (URL exactas):**

- https://api.worldbank.org/v2/country/PAN;CRI;COL;DOM;MEX;GTM/indicator/NY.GDP.MKTP.KD.ZG?format=json&date=2010:2024&per_page=1000
- https://api.worldbank.org/v2/country/PAN;CRI;COL;DOM;MEX;GTM/indicator/FP.CPI.TOTL.ZG?format=json&date=2010:2024&per_page=1000
- https://api.worldbank.org/v2/country/PAN;CRI;COL;DOM;MEX;GTM/indicator/SL.UEM.TOTL.ZS?format=json&date=2010:2024&per_page=1000
- https://api.worldbank.org/v2/country/PAN;CRI;COL;DOM;MEX;GTM/indicator/SP.POP.TOTL?format=json&date=2010:2024&per_page=1000
- https://api.worldbank.org/v2/country/PAN;CRI;COL;DOM;MEX;GTM/indicator/IT.NET.USER.ZS?format=json&date=2010:2024&per_page=1000
- https://api.worldbank.org/v2/country/PAN;CRI;COL;DOM;MEX;GTM/indicator/NE.EXP.GNFS.ZS?format=json&date=2010:2024&per_page=1000
- https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2024-01-01&endtime=2025-01-01&minlatitude=5&maxlatitude=12&minlongitude=-86&maxlongitude=-76&minmagnitude=3&orderby=time
- https://www.tvn-2.com/rss/
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama&mode=ArtList&format=json&maxrecords=250&startdatetime=20261001212422&enddatetime=20261006212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama&mode=ArtList&format=json&maxrecords=250&startdatetime=20260926212422&enddatetime=20261001212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama&mode=ArtList&format=json&maxrecords=250&startdatetime=20260921212422&enddatetime=20260926212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama&mode=ArtList&format=json&maxrecords=250&startdatetime=20260916212422&enddatetime=20260921212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama&mode=ArtList&format=json&maxrecords=250&startdatetime=20260911212422&enddatetime=20260916212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama&mode=ArtList&format=json&maxrecords=250&startdatetime=20260906212422&enddatetime=20260911212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+logistica&mode=ArtList&format=json&maxrecords=250&startdatetime=20261001212422&enddatetime=20261006212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+logistica&mode=ArtList&format=json&maxrecords=250&startdatetime=20260926212422&enddatetime=20261001212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+logistica&mode=ArtList&format=json&maxrecords=250&startdatetime=20260921212422&enddatetime=20260926212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+logistica&mode=ArtList&format=json&maxrecords=250&startdatetime=20260916212422&enddatetime=20260921212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+logistica&mode=ArtList&format=json&maxrecords=250&startdatetime=20260911212422&enddatetime=20260916212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+logistica&mode=ArtList&format=json&maxrecords=250&startdatetime=20260906212422&enddatetime=20260911212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+canal&mode=ArtList&format=json&maxrecords=250&startdatetime=20261001212422&enddatetime=20261006212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+canal&mode=ArtList&format=json&maxrecords=250&startdatetime=20260926212422&enddatetime=20261001212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+canal&mode=ArtList&format=json&maxrecords=250&startdatetime=20260921212422&enddatetime=20260926212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+canal&mode=ArtList&format=json&maxrecords=250&startdatetime=20260916212422&enddatetime=20260921212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+canal&mode=ArtList&format=json&maxrecords=250&startdatetime=20260911212422&enddatetime=20260916212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+canal&mode=ArtList&format=json&maxrecords=250&startdatetime=20260906212422&enddatetime=20260911212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+turismo&mode=ArtList&format=json&maxrecords=250&startdatetime=20261001212422&enddatetime=20261006212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+turismo&mode=ArtList&format=json&maxrecords=250&startdatetime=20260926212422&enddatetime=20261001212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+turismo&mode=ArtList&format=json&maxrecords=250&startdatetime=20260921212422&enddatetime=20260926212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+turismo&mode=ArtList&format=json&maxrecords=250&startdatetime=20260916212422&enddatetime=20260921212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+turismo&mode=ArtList&format=json&maxrecords=250&startdatetime=20260911212422&enddatetime=20260916212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+turismo&mode=ArtList&format=json&maxrecords=250&startdatetime=20260906212422&enddatetime=20260911212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+economia&mode=ArtList&format=json&maxrecords=250&startdatetime=20261001212422&enddatetime=20261006212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+economia&mode=ArtList&format=json&maxrecords=250&startdatetime=20260926212422&enddatetime=20261001212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+economia&mode=ArtList&format=json&maxrecords=250&startdatetime=20260921212422&enddatetime=20260926212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+economia&mode=ArtList&format=json&maxrecords=250&startdatetime=20260916212422&enddatetime=20260921212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+economia&mode=ArtList&format=json&maxrecords=250&startdatetime=20260911212422&enddatetime=20260916212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+economia&mode=ArtList&format=json&maxrecords=250&startdatetime=20260906212422&enddatetime=20260911212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+sismo&mode=ArtList&format=json&maxrecords=250&startdatetime=20261001212422&enddatetime=20261006212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+sismo&mode=ArtList&format=json&maxrecords=250&startdatetime=20260926212422&enddatetime=20261001212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+sismo&mode=ArtList&format=json&maxrecords=250&startdatetime=20260921212422&enddatetime=20260926212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+sismo&mode=ArtList&format=json&maxrecords=250&startdatetime=20260916212422&enddatetime=20260921212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+sismo&mode=ArtList&format=json&maxrecords=250&startdatetime=20260911212422&enddatetime=20260916212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=Panama+sismo&mode=ArtList&format=json&maxrecords=250&startdatetime=20260906212422&enddatetime=20260911212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=sourcecountry%3Apanama&mode=ArtList&format=json&maxrecords=250&startdatetime=20261001212422&enddatetime=20261006212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=sourcecountry%3Apanama&mode=ArtList&format=json&maxrecords=250&startdatetime=20260926212422&enddatetime=20261001212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=sourcecountry%3Apanama&mode=ArtList&format=json&maxrecords=250&startdatetime=20260921212422&enddatetime=20260926212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=sourcecountry%3Apanama&mode=ArtList&format=json&maxrecords=250&startdatetime=20260916212422&enddatetime=20260921212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=sourcecountry%3Apanama&mode=ArtList&format=json&maxrecords=250&startdatetime=20260911212422&enddatetime=20260916212422
- https://api.gdeltproject.org/api/v2/doc/doc?query=sourcecountry%3Apanama&mode=ArtList&format=json&maxrecords=250&startdatetime=20260906212422&enddatetime=20260911212422
