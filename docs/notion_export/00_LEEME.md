# Export para Notion

Notion es obligatorio en el reto y la carga es **manual**. Estos archivos están listos para importar: en Notion, *Importar → Markdown y CSV*. También se pueden pegar.

| Página obligatoria (sección 5 del reto) | Archivo |
|---|---|
| Inicio del reto | `01_inicio_del_reto.md` |
| Plan y decisiones | `02_plan_y_decisiones.md` (convertir la tabla de backlog en base de datos) |
| Catálogo de datos | `03_catalogo_de_datos.md` |
| Diseño de solución | `04_diseno_de_solucion.md` |
| Casos y evidencias | `05_casos_y_evidencias.md` (7 fichas; se genera, ver abajo) |
| Pruebas y métricas | `06_pruebas_y_metricas.md` |
| Riesgos y ética | `07_riesgos_y_etica.md` |
| Presentación al jurado | `08_presentacion_al_jurado.md` |

### Páginas generadas desde el sistema (no se editan a mano)

Se regeneran con `cd backend; .\.venv\Scripts\python -m app.notion_export --correr` (corre T01–T10 y exporta, sin red):

| Página | Archivo | Fuente |
|---|---|---|
| Matriz T01–T10 con resultado observado + agente vs baseline | `10_matriz_T01_T10.md` | Ejecución real de `tests/test_reto.py` (Modo jurado) y `eval/results.json` |
| Catálogo de datos | `11_catalogo_generado.md` | `data/raw/manifest.json` |
| Casos y evidencias (7 fichas, una insuficiente) | `05_casos_y_evidencias.md` | Pipeline sobre el snapshot + revisiones guardadas en la base |
| Bitácora de decisiones y revisiones humanas | `12_bitacora_y_revisiones.md` | Tabla `audit` de `data/app.db` y `docs/09_DECISIONS.md` |

Las revisiones humanas que aparecen son las registradas en la base local al exportar: regenera después de hacer las revisiones reales.

## Lo que debes completar en Notion

- Persona revisora y decisión de cada ficha en «Casos y evidencias». No se inventan.
- Acceso del jurado al espacio y URL del espacio en «Inicio del reto».
- Registro "durante la ejecución": las fechas del backlog y del changelog vienen de git. Agrega las tuyas a medida que avances.
- Capturas o embeds de la demo. Se pueden usar los enlaces directos del README, por ejemplo `#/ficha/SINT-S-CON-001/resumen`.
