#!/usr/bin/env python3
"""Descarga el snapshot público a data/raw/ (solo stdlib).
Uso: python data/scripts/download_snapshot.py [wb|usgs|news|all]
Corre en TU máquina (necesita internet). RSS de TVN: TVN_RSS_URL o, por defecto, la referencia [2] del PDF.
De TVN solo se guardan metadatos (título, URL, fecha); no se guarda descripción ni cuerpo."""
import csv, hashlib, json, os, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "raw"
RAW.mkdir(parents=True, exist_ok=True)
NOW = datetime.now(timezone.utc)
STAMP = NOW.isoformat(timespec="seconds")
PAISES = ["PAN", "CRI", "COL", "DOM", "MEX", "GTM"]
IND = {"NY.GDP.MKTP.KD.ZG": "% anual", "FP.CPI.TOTL.ZG": "% anual", "SL.UEM.TOTL.ZS": "% fuerza laboral",
       "SP.POP.TOTL": "personas", "IT.NET.USER.ZS": "% población", "NE.EXP.GNFS.ZS": "% del PIB"}
GDELT_Q = ["Panama", "Panama logistica", "Panama canal", "Panama turismo", "Panama economia", "Panama sismo", "sourcecountry:panama"]
TVN_RSS_DEFAULT = "https://www.tvn-2.com/rss/"  # referencia [2] de docs/reto_TVN.pdf
DIAS = int(os.getenv("NEWS_DAYS", "30"))
CONSULTAS = []
FALLIDAS = []


def get(url):
    CONSULTAS.append(url)
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "hackiathon-tvn/0.1"}), timeout=60) as r:
        return r.read()


def wb():
    vals = {}
    for ind in IND:
        d = json.loads(get(f"https://api.worldbank.org/v2/country/{';'.join(PAISES)}/indicator/{ind}?format=json&date=2010:2024&per_page=1000"))
        for x in (d[1] or []):
            vals[(x["countryiso3code"], ind, int(x["date"]))] = x["value"]
    with open(RAW / "indicadores.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pais_iso3", "indicador_id", "anio", "valor", "unidad", "fuente_url", "fecha_extraccion", "licencia"])
        for p in PAISES:  # cuadrícula completa; faltantes quedan vacíos (nulos), nunca 0
            for ind in IND:
                for y in range(2010, 2025):
                    v = vals.get((p, ind, y))
                    w.writerow([p, ind, y, "" if v is None else v, IND[ind],
                                f"https://api.worldbank.org/v2/country/{p}/indicator/{ind}", STAMP, "CC BY 4.0"])


def usgs():
    q = dict(format="geojson", starttime="2024-01-01", endtime="2025-01-01", minlatitude=5, maxlatitude=12,
             minlongitude=-86, maxlongitude=-76, minmagnitude=3, orderby="time")  # endtime exclusivo = todo 2024
    (RAW / "eventos.geojson").write_bytes(get("https://earthquake.usgs.gov/fdsnws/event/1/query?" + urllib.parse.urlencode(q)))


def nid(prefix, url):
    return prefix + hashlib.sha1(url.encode()).hexdigest()[:10]


def news():
    rows, seen = [], set()
    rss = os.getenv("TVN_RSS_URL") or TVN_RSS_DEFAULT
    if rss:
        for it in ET.fromstring(get(rss)).iter("item"):
            url, title = (it.findtext("link") or "").strip(), (it.findtext("title") or "").strip()
            pub = it.findtext("pubDate")
            if url in seen: continue
            seen.add(url)
            fp = parsedate_to_datetime(pub).astimezone(timezone.utc).isoformat() if pub else ""
            rows.append([nid("T", url), title, url, "tvn.com.pa", "es", fp, "", STAMP, "", "tvn_rss", "titular/metadatos"])
    else:
        print("AVISO: falta TVN_RSS_URL; el reto exige >=20 registros de TVN.")
    for q in GDELT_Q:
        for i in range(0, DIAS, 5):  # ventanas de 5 días (límite 250 por consulta)
            a, b = NOW - timedelta(days=i + 5), NOW - timedelta(days=i)
            u = "https://api.gdeltproject.org/api/v2/doc/doc?" + urllib.parse.urlencode({
                "query": q, "mode": "ArtList", "format": "json", "maxrecords": 250,
                "startdatetime": a.strftime("%Y%m%d%H%M%S"), "enddatetime": b.strftime("%Y%m%d%H%M%S")})
            arts = []
            for intento in range(4):  # GDELT exige >=5 s entre consultas; ante 429 se espera más
                try:
                    arts = json.loads(get(u)).get("articles", []); break
                except Exception as e:
                    print("GDELT reintento:", q, i, intento, e); time.sleep(15 * (intento + 1))
            else:
                FALLIDAS.append(f"{q} ventana {i}-{i + 5} días")
            time.sleep(6)  # cortesía con la API
            for x in arts:
                if not x.get("url") or not x.get("title") or x["url"] in seen: continue
                seen.add(x["url"])
                det = datetime.strptime(x["seendate"], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).isoformat()
                # GDELT no da fecha de publicación: queda vacía; seendate = detección
                rows.append([nid("G", x["url"]), x["title"], x["url"], x.get("domain", ""), x.get("language", ""), "", det, STAMP, "", "gdelt", "titular/metadatos"])
    with open(RAW / "noticias.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id_noticia", "titulo", "url", "medio", "idioma", "fecha_publicacion", "fecha_deteccion", "fecha_extraccion", "tema", "origen", "alcance_texto"])
        w.writerows(rows)


def manifest():
    files = {}
    for p in sorted(RAW.glob("*")):
        if p.name == "manifest.json": continue
        n = len(json.loads(p.read_text(encoding="utf-8"))["features"]) if p.suffix == ".geojson" else max(0, len(p.read_text(encoding="utf-8").splitlines()) - 1)
        files[p.name] = {"registros": n, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    (RAW / "manifest.json").write_text(json.dumps({
        "version": "v1", "fecha_corte_UTC": STAMP, "consultas": CONSULTAS, "consultas_fallidas": FALLIDAS, "archivos": files,
        "licencia_condiciones": "Banco Mundial CC BY 4.0; USGS y GDELT: revisar condiciones; TVN: solo metadatos, sin republicar contenido",
        "ventana_noticias_dias": DIAS,
        "nota_intervalo": "El PDF propone [2024-01-01, 2025-10-01) pero también 'últimos 30 días'; GDELT DOC solo cubre ~3 meses. Se usa la ventana reciente (ver docs/09_DECISIONS.md).",
        "transformaciones": ["Cuadrícula país×indicador×año completa con nulos explícitos", "Dedupe por URL", "Unidades de indicadores asignadas por tabla fija", "TVN: solo título/URL/pubDate (sin descripción)", "GDELT: fecha_publicacion vacía; seendate -> fecha_deteccion"]},
        ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    t = sys.argv[1] if len(sys.argv) > 1 else "all"
    if t in ("wb", "all"): wb()
    if t in ("usgs", "all"): usgs()
    if t in ("news", "all"): news()
    manifest()
    print("Listo. Revisa data/raw/manifest.json")
