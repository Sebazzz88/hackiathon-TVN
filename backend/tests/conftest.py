"""Se carga antes que cualquier prueba: la base de datos por defecto de TODA la suite es temporal.
Así ninguna prueba puede escribir en data/app.db (donde están las revisiones reales)."""
import os
import tempfile

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(prefix="tvn-pruebas-"), "pruebas.db")
os.environ.setdefault("LLM_OFFLINE", "1")  # las pruebas nunca llaman a un modelo real
