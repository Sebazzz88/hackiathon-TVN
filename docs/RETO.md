# RETO TVN — resumen operativo (fuente: docs/reto_TVN.pdf)

**Objetivo:** prototipo que convierte noticias públicas + indicadores oficiales en bandeja priorizada, fichas de evidencia y borradores para decisión humana. Modalidad elegida: **TVN editorial**. Todo hecho → fuente, fecha y alcance.

## Obligatorio (MVP)
- Ingesta ≥2 familias: noticias (TVN RSS ≥20 + GDELT; meta 200, mínimo 100) y datos oficiales (Banco Mundial 6 países × 6 indicadores × 2010–2024 = 1.350 celdas, nulos explícitos). USGS 2024 caja lat 5–12, lon −86/−76, M≥3: solo hechos sísmicos.
- Flujo 7 etapas: Cargar (reporte de calidad) → Organizar (6 temas: economía, logística/Canal, turismo, servicios públicos, eventos naturales, regulación; agrupar eventos) → Contextualizar (indicador con período/unidad/límites; no forzar) → Priorizar (P=30R+25I+20U+15N+10E; bajo [0,40) medio [40,70) alto [70,100]; empate: U, luego ID; versión de reglas) → Explicar (qué se reporta, quién, qué respalda, qué falta, acción) → Producir (borrador con cita por afirmación; hecho/declaración/inferencia/hipótesis) → Revisar (5 estados: nuevo, en revisión, requiere evidencia, aprobado como borrador, descartado).
- Estado de evidencia independiente del puntaje: insuficiente / parcial / suficiente para borrador.
- Salida TVN: brief ≤250 palabras, título, enfoque de interés público, 3 preguntas, fuentes y verificaciones pendientes, guion 45–60 s, copy ≤80 palabras. Leyenda "basado únicamente en titular/metadatos".
- IA sustantiva (NLP/ML, no IF/ELSE) + baseline simple comparado. LLM: instrucciones separadas de fuentes, salida estructurada con citas. Documentar modelo, prompts, costo, límites.
- Seguridad: anti-alucinación, anti-inyección, privacidad, derechos, credenciales fuera del código.
- Contrato: noticias.csv, indicadores.csv, eventos.geojson, fichas.jsonl, manifest.json (SHA-256). UTF-8, ISO 8601 UTC, hora Panamá en UI, fecha_publicacion ≠ seendate. Intervalo [2024-01-01, 2025-10-01) según "normas de extracción propuestas".
- benchmark.jsonl: 60 consultas (30 sustentadas, 10 contradicción, 10 sin respuesta, 10 adversariales); 40 dev / 20 reservadas; etiquetas por revisión humana; sintéticos marcados.

## Pruebas T01–T10
T01 fechas inválidas/nulos sin bloquear · T02 3 registros mismo evento sin triplicar · T03 noticia antigua recirculada · T04 cifra anual BM con país/año/unidad · T05 dos afirmaciones incompatibles visibles · T06 abstención sin inventar · T07 fuente con inyección · T08 prioridad alta no habilita publicar · T09 brief con citas y tipos · T10 demo sin internet.

## Casos de uso
CU-01 top 5 Panamá y por qué · CU-02 tema económico + serie oficial sin confundir año · CU-03 repetición ≠ corroboración (agencia replicada = 1) · CU-04 cifra inexistente/contradicción → abstención · CU-05 banca logística (opcional).

## Métricas (numerador/denominador)
Cobertura de citas 100% · validez ≥90% (≥30 afirmaciones, revisión humana) · abstención ≥80% · macro-F1 clasificación/agrupación · Precision@5 (exploratoria sin especialista) · mediana ≤15 s y p95.

## Entregables
Prototipo reproducible offline · GitHub (README, instalación, deps fijadas, .env.example, pruebas) · paquete de datos (snapshot, diccionario, manifest, licencias, benchmark dev) · Notion (Inicio, Plan ≥8 tareas y ≥3 decisiones, Catálogo, Diseño, ≥5 fichas incl. 1 insuficiente, matriz T01–T10, Riesgos, Pitch 10 min).

## Rúbrica (100)
Utilidad 20 · Prototipo/flujo 20 · Uso IA 15 · Evidencias/explicabilidad 15 · Notion 15 · Calidad técnica 10 · Seguridad/ética 5.
