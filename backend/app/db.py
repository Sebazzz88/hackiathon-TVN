"""SQLite del Copiloto. Conexiones que se cierran, modo WAL (lecturas y escrituras no se bloquean) y columnas de
orden indexadas: la bandeja trae solo las N fichas pedidas con una consulta SQL, no las 700+ del snapshot."""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_d = Path(os.getenv("DATA_DIR") or ROOT / "data")
DATA_DIR = _d if _d.is_absolute() else ((ROOT / "backend" / _d).resolve() if (ROOT / "backend" / _d).exists() else _d.resolve())
DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "app.db"))


@contextmanager
def conn():
    """Conexión con commit al salir y CIERRE garantizado (sqlite3 por sí solo no cierra en `with`)."""
    c = sqlite3.connect(DB_PATH, timeout=30)
    c.row_factory = sqlite3.Row
    try:
        with c:
            yield c
    finally:
        c.close()


def _columnas(c, tabla):
    return {r["name"] for r in c.execute(f"PRAGMA table_info({tabla})")}


def init():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with conn() as c:
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("CREATE TABLE IF NOT EXISTS fichas(id_caso TEXT PRIMARY KEY, data TEXT NOT NULL)")
        c.execute("CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, accion TEXT, id_caso TEXT, detalle TEXT)")
        # migración de bases creadas por versiones anteriores: columnas de orden + relleno desde el JSON
        cols = _columnas(c, "fichas")
        for nombre, tipo in (("puntaje", "REAL"), ("u", "REAL"), ("sint", "INTEGER"), ("tema", "TEXT"), ("fecha", "TEXT")):
            if nombre not in cols:
                c.execute(f"ALTER TABLE fichas ADD COLUMN {nombre} {tipo}")
        for r in c.execute("SELECT id_caso, data FROM fichas WHERE puntaje IS NULL OR tema IS NULL").fetchall():
            d = json.loads(r["data"])
            c.execute("UPDATE fichas SET puntaje=?, u=?, sint=?, tema=?, fecha=? WHERE id_caso=?",
                      (d.get("puntaje", 0), d.get("componentes", {}).get("U", 0), int(bool(d.get("sintetico"))),
                       d.get("tema", ""), d.get("fecha_ultima", ""), r["id_caso"]))
        c.execute("CREATE INDEX IF NOT EXISTS ix_fichas_orden ON fichas(sint, puntaje DESC, u DESC, id_caso)")


def _fila(f):
    return (f.id_caso, f.model_dump_json(), f.puntaje, f.componentes.U, int(bool(f.sintetico)), f.tema or "", f.fecha_ultima or "")


_INS = "INSERT OR REPLACE INTO fichas(id_caso,data,puntaje,u,sint,tema,fecha) VALUES(?,?,?,?,?,?,?)"


def save(f):
    with conn() as c:
        c.execute(_INS, _fila(f))


def replace_all(fichas):
    """Sustituye todas las fichas en UNA transacción: quien lee nunca ve la tabla vacía a medio sembrar."""
    filas = [_fila(f) for f in fichas]
    with conn() as c:
        c.execute("DELETE FROM fichas")
        c.executemany(_INS, filas)


def get(id_caso):
    with conn() as c:
        r = c.execute("SELECT data FROM fichas WHERE id_caso=?", (id_caso,)).fetchone()
    return json.loads(r["data"]) if r else None


def count():
    with conn() as c:
        return c.execute("SELECT COUNT(*) FROM fichas").fetchone()[0]


def inbox(limit, sint=None, tema=None, desde=None):
    """(total, [ficha dict]) de las `limit` fichas con más puntaje. Orden del reto: puntaje desc, urgencia desc, ID.
    sint=None -> todas; True/False -> solo sintéticas / solo reales. tema: filtra por tema. desde: ISO UTC mínimo."""
    conds, args = [], []
    if sint is not None:
        conds.append("sint=?"); args.append(int(bool(sint)))
    if tema:
        conds.append("tema=?"); args.append(tema)
    if desde:
        conds.append("fecha>=?"); args.append(desde)
    donde = ("WHERE " + " AND ".join(conds)) if conds else ""
    with conn() as c:
        total = c.execute(f"SELECT COUNT(*) FROM fichas {donde}", args).fetchone()[0]
        rows = c.execute(f"SELECT data FROM fichas {donde} ORDER BY puntaje DESC, u DESC, id_caso ASC LIMIT ?",
                         args + [limit]).fetchall()
    return total, [json.loads(r["data"]) for r in rows]


def all_fichas():
    with conn() as c:
        return [json.loads(r["data"]) for r in c.execute("SELECT data FROM fichas")]


def log(accion, id_caso="", detalle=""):
    with conn() as c:
        c.execute("INSERT INTO audit(ts,accion,id_caso,detalle) VALUES(?,?,?,?)",
                  (datetime.now(timezone.utc).isoformat(timespec="seconds"), accion, id_caso, detalle))


def audit():
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 200")]


def validador_totales():
    """Suma de todo lo que el validador ha revisado desde que existe la base: emitidas, válidas, eliminadas y por qué."""
    tot = {"revisiones": 0, "emitidas": 0, "validas": 0, "eliminadas": 0, "por_codigo": {}}
    with conn() as c:
        filas = c.execute("SELECT detalle FROM audit WHERE accion='validador'").fetchall()
    for r in filas:
        try:
            d = json.loads(r["detalle"])
        except (TypeError, ValueError):
            continue
        tot["revisiones"] += 1
        for k in ("emitidas", "validas", "eliminadas"):
            tot[k] += int(d.get(k, 0))
        for cod, n in d.get("por_codigo", {}).items():
            tot["por_codigo"][cod] = tot["por_codigo"].get(cod, 0) + int(n)
    return tot


def set_meta(k, v):
    with conn() as c:
        c.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (k, v))


def get_meta(k):
    with conn() as c:
        r = c.execute("SELECT v FROM meta WHERE k=?", (k,)).fetchone()
    return r["v"] if r else None
