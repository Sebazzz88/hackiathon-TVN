import json, os, sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_d = Path(os.getenv("DATA_DIR") or ROOT / "data")
DATA_DIR = _d if _d.is_absolute() else ((ROOT / "backend" / _d).resolve() if (ROOT / "backend" / _d).exists() else _d.resolve())
DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "app.db"))


def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with conn() as c:
        c.execute("CREATE TABLE IF NOT EXISTS fichas(id_caso TEXT PRIMARY KEY, data TEXT NOT NULL)")
        c.execute("CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, accion TEXT, id_caso TEXT, detalle TEXT)")


def save(f):
    with conn() as c:
        c.execute("INSERT OR REPLACE INTO fichas VALUES(?,?)", (f.id_caso, f.model_dump_json()))


def get(id_caso):
    with conn() as c:
        r = c.execute("SELECT data FROM fichas WHERE id_caso=?", (id_caso,)).fetchone()
    return json.loads(r["data"]) if r else None


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


def clear():
    with conn() as c:
        c.execute("DELETE FROM fichas")


def set_meta(k, v):
    with conn() as c:
        c.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (k, v))


def get_meta(k):
    with conn() as c:
        r = c.execute("SELECT v FROM meta WHERE k=?", (k,)).fetchone()
    return r["v"] if r else None
