# Auditoría final contra docs/RETO.md

Fecha: 2026-10-06. Rama `feat/agente`. Verificado con 24 pruebas (0 fallos, 0 omitidas), `eval/run_eval.py` y una instalación desde un clon limpio de GitHub.

## Requisitos

| Requisito | Implementado | Verificado | Observaciones |
|---|---|---|---|
| Ingesta noticias (≥ 100, ≥ 20 TVN) | Sí | Sí: 875 válidas, 152 TVN | GDELT con 29 ventanas fallidas por HTTP 429, registradas en el manifest |
| Datos oficiales (Banco Mundial) | Sí | Sí: 540/540 celdas | El PDF dice 1.350; la cuadrícula descrita da 540 (D04) |
| USGS solo para sismos | Sí | Sí: 82 eventos; solo con tema natural y palabra "sismo" | |
| Snapshot congelado + manifest SHA-256 | Sí | Sí: hashes del commit = manifest | `.gitattributes` evita conversión de líneas |
| 1 Cargar: reporte de calidad | Sí | T01 | Errores separados, nulos conservados |
| 2 Organizar: 6 temas + agrupación | Sí | macro-F1 test 0,44 (baseline 0,395); agrupación F1 0,875 (0,615) | La clasificación con titulares mejora poco |
| 3 Contextualizar sin forzar | Sí | T04 | Sin relación → se declara la ausencia |
| 4 Priorizar 30R+25I+20U+15N+10E, bandas, desempate | Sí | T08, `test_formula_y_bandas` | Pesos del reto sin cambios (`reglas-v1`) |
| Estado de evidencia independiente | Sí | T02, T05, T07, T08 | |
| 5 Explicar: ficha con 5 preguntas | Sí | UI + `05_casos_y_evidencias.md` | |
| 6 Producir: paquete TVN con citas y tipos | Sí | T09; 195/195 afirmaciones con cita | Guion de plantilla en 45–60 s solo en 9/18 (falta material; se avisa) |
| Leyenda "basado únicamente en titular/metadatos" | Sí | T09 | |
| 7 Revisar: 5 estados, revisor, comentario | Sí | `test_bandeja_…`; UI | Aprobar no publica; bloqueado con evidencia insuficiente |
| Consultas en español con abstención | Sí | T06; benchmark 20/20 abstención correcta | |
| Contradicciones visibles | Sí | T05; 10/10 en benchmark | Solo contradicciones numéricas |
| Agencia replicada = 1 | Sí | T02 | Detección por agencia citada o texto casi idéntico |
| Anti-inyección | Sí | T07 + prueba con LLM simulado | Patrones + aislamiento `<DATO>` + validador |
| LLM con caché y salida JSON | Sí | Solo con cliente simulado | **No probado con clave real**; no hay caché de borradores |
| Sin internet (T10) | Sí | T10 | Plantilla + caché + respaldo léxico |
| Baseline comparado | Sí | `eval/run_eval.py` | Palabras clave, reglas, fecha |
| Benchmark 60 (30/10/10/10; 40/20) | Sí | `eval/benchmark.jsonl` | Etiquetas **pendientes de revisión humana**; reservado no ciego |
| Métricas con numerador/denominador | Sí | `eval/resultados/` | Validez de sustento y Precision@5 **pendientes** |
| README, instalación, dependencias fijadas, .env.example, pruebas | Sí | Clon limpio de GitHub: instala, descarga el modelo, pasa las pruebas, compila, la evaluación da **las mismas métricas** y el backend arranca en modo live con el mismo top 5 | `iniciar.ps1` sin ejecutar de punta a punta porque abre ventanas; sus comandos se probaron uno por uno |
| Docs 01–12 | Sí | | 12_AI_USAGE: Codex y ChatGPT **pendientes** de completar por el autor |
| Notion (8 páginas, ≥ 8 tareas, ≥ 3 decisiones, ≥ 5 fichas, matriz, pitch) | Contenido listo en `docs/notion_export/` | **No cargado** | **Condición de admisión** |

## Puntaje estimado (rúbrica de 100, mirada de jurado)

| Dimensión | Peso | Nota 0–5 | Puntos | Por qué |
|---|---|---|---|---|
| Utilidad para TVN | 20 | 4 | 16 | Usuario y flujo claros; impacto no medido |
| Prototipo y flujo completo | 20 | 4 | 16 | Flujo completo con datos comunes; borradores solo por plantilla |
| Uso efectivo de IA | 15 | 3,5 | 10,5 | Embeddings locales + baseline medido; clasificación débil; LLM sin demostrar |
| Evidencias y explicabilidad | 15 | 4,5 | 13,5 | Citas, puntaje reproducible, contradicciones y abstención |
| Notion: ejecución y pitch | 15 | 0 → 3,5 | 0 → 10,5 | 0 hoy; ~10 si se carga bien con registro durante el evento |
| Calidad técnica y evaluación | 10 | 4 | 8 | Reproducible, 24 pruebas, métricas verificables; etiquetas sin revisar |
| Seguridad, privacidad y ética | 5 | 4 | 4 | Controles operativos y probados |
| **Total** | 100 | | **68 hoy → ~78 con Notion** | Rango razonable ±6. Sin Notion la entrega no se admite |

## Riesgos

- 🔴 **Notion sin cargar.** Sin el espacio, el acceso del jurado y el pitch desde Notion, la entrega no se admite.
- 🔴 **Etiquetas sin revisión humana.** Todas las métricas del benchmark son preliminares; un jurado puede descartarlas.
- 🟠 **LLM no probado con clave real** y sin borradores en caché: la demo muestra solo la plantilla.
- 🟠 **Precision@5 y validez de sustento pendientes:** son métricas pedidas explícitamente.
- 🟠 **Repositorio y PR:** el trabajo está en `feat/agente`; el jurado verá `main` si no se fusiona. Confirmar que el jurado tenga acceso al repo.
- 🟠 **Guion corto** en temas de una sola fuente (9/18 en 45–60 s).
- 🟡 Cobertura de GDELT incompleta por el límite de tasa.
- 🟡 El conjunto reservado no es ciego.
- 🟡 Docker no probado.
- 🟡 12_AI_USAGE: falta completar Codex y ChatGPT.

## LO QUE TÚ TIENES QUE HACER AHORA

Todos los comandos son de PowerShell, desde la carpeta del repo.

**1. Encender y revisar la demo**

```powershell
powershell -ExecutionPolicy Bypass -File .\iniciar.ps1
```

**2. (Opcional, recomendado) Borradores con Claude y caché para la demo offline.** Edita `.env` y pon `LLM_API_KEY=tu-clave`. Luego, con el backend encendido:

```powershell
foreach ($id in "EV-G226d8217c0","EV-Gb01bc434a8","EV-G97e3e7b0a7","EV-G1454ad17a8","SINT-S-CON-001") {
  Invoke-RestMethod -Method Post "http://localhost:8000/api/fichas/$id/draft" | Select-Object id_caso, @{n="generador";e={$_.borrador.generador}}
}
git add data/cache/llm; git commit -m "data: caché de borradores LLM para demo offline"; git push origin feat/agente
```

**3. Revisar las etiquetas.** Abre y corrige las columnas `tema_humano`, `mismo_evento` y `esperado`. Escribe tu nombre en `revisado_por`.

```powershell
start eval\etiquetas_temas.csv
start eval\etiquetas_pares.csv
notepad eval\benchmark.jsonl
```

**4. Validez de sustento.** Marca al menos 30 filas como `respaldada` o `no_respaldada`.

```powershell
start eval\resultados\afirmaciones_para_revision.csv
```

**5. Precision@5.** Pide a un editor que elija 5 temas **sin ver el ranking**. Guarda sus IDs:

```powershell
'{"ids": ["EV-...", "EV-...", "EV-...", "EV-...", "EV-..."], "editor": "Nombre", "fecha": "2026-10-07"}' | Out-File -Encoding utf8 eval\seleccion_editor.json
```

**6. Volver a evaluar y subir**

```powershell
backend\.venv\Scripts\python eval\run_eval.py
cd backend; .\.venv\Scripts\python -m pytest -q; cd ..
git add eval docs; git commit -m "eval: etiquetas revisadas y métricas finales"; git push origin feat/agente
```

**7. Notion (obligatorio).** Importa `docs\notion_export\*.md` (*Importar → Markdown*), completa revisor y decisión en las fichas y da acceso al jurado. Guía: `docs\notion_export\00_LEEME.md`.

**8. Completar `docs\12_AI_USAGE.md`** con lo que hiciste con Codex y ChatGPT.

**9. Fusionar a `main` antes del jueves 18:00.** Crea el PR en https://github.com/Sebazzz88/hackiathon-TVN/compare/main...feat/agente, revísalo y fusiónalo.

**10. Ensayar el pitch** con `docs\notion_export\08_presentacion_al_jurado.md`, sin internet.
