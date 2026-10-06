import json, os, sqlite3
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", "../data"))
DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "app.db"))


def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with conn() as c:
        c.execute("CREATE TABLE IF NOT EXISTS fichas(id_caso TEXT PRIMARY KEY, data TEXT NOT NULL)")
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
