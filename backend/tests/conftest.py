"""Se carga antes que cualquier prueba: la base de datos por defecto de TODA la suite es temporal.
Así ninguna prueba puede escribir en data/app.db (donde están las revisiones reales)."""
import os
import tempfile

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(prefix="tvn-pruebas-"), "pruebas.db")
os.environ.setdefault("LLM_OFFLINE", "1")  # las pruebas nunca llaman a un modelo real


def base_live(mp, nombre):
    """Base temporal propia en modo live, sembrada con todas las fichas del pipeline y con los metadatos al día (así el
    arranque de la app no la vuelve a sembrar). `mp`: el MonkeyPatch de la prueba o del módulo, que la deshace al final."""
    from app import db, main
    from app.agent import pipeline
    mp.setattr(db, "DB_PATH", os.path.join(tempfile.mkdtemp(), nombre))
    mp.setattr(main.agent, "AGENT_MODE", "live")
    db.init()
    db.replace_all(pipeline.seleccionar(pipeline.analizar()["fichas"]))  # seleccionar() ya aplica el puntaje
    db.set_meta("agent_mode", "live")
    db.set_meta("fichas_version", main.FICHAS_VERSION)
