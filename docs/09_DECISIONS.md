# Decisiones

> Fecha, decisión, alternativas, responsable

Responsable de todas: Sebastián (equipo de una persona), con asistencia de Claude Code. Fechas en hora de Panamá.

| # | Fecha | Decisión | Alternativas | Justificación |
|---|---|---|---|---|
| D01 | 2026-10-06 | Modalidad TVN editorial únicamente | TVN + banca | El reto recomienda una modalidad y un recorrido convincente; equipo de una persona |
| D02 | 2026-10-06 | RSS de TVN = `https://www.tvn-2.com/rss/` (referencia [2] del PDF) y solo título, URL y fecha | Guardar descripción del RSS | El PDF aclara que el RSS no implica licencia sobre el contenido; la descripción es texto editorial |
| D03 | 2026-10-06 | Ventana de noticias = últimos 30 días; no se aplica el intervalo [2024-01-01, 2025-10-01) | Aplicar el intervalo y quedarse sin noticias | El PDF pide ambas cosas; GDELT DOC solo cubre ~3 meses y la extracción es de octubre 2026. Se registra en el manifest |
| D04 | 2026-10-06 | Banco Mundial: cuadrícula completa de 540 celdas (6 × 6 × 15) | Buscar 1.350 celdas | 1.350 no corresponde a la cuadrícula descrita; se documenta la discrepancia del PDF |
| D05 | 2026-10-06 | Embeddings locales con fastembed/ONNX (`paraphrase-multilingual-MiniLM-L12-v2`, 0,22 GB) | sentence-transformers + PyTorch; API de embeddings | Funciona sin internet (T10), ~10× menos peso que PyTorch, multilingüe (GDELT trae español, inglés, alemán, chino) |
| D06 | 2026-10-06 | Réplica de agencia = agencia citada o texto casi idéntico (Jaccard ≥ 0,8) con las mismas cifras | Similitud semántica ≥ 0,93 | Medido: titulares distintos del mismo hecho dan 0,89–0,95 de similitud; el criterio semántico contaba reporteo propio como réplica |
| D07 | 2026-10-06 | Clasificación con umbral: similitud ≥ 0,40 y margen ≥ 0,05; si no, "otros" | Asignar siempre el tema más cercano | Medido: noticias internacionales caían en economía con similitud 0,17–0,34 |
| D08 | 2026-10-06 | Titulares iguales salvo cifras = mismo evento | Solo similitud semántica | Cambiar la cifra baja la similitud bajo 0,80 y ocultaba contradicciones (detectado por la prueba T05) |
| D09 | 2026-10-06 | Vínculo con Panamá: 1,0 si el titular menciona Panamá o una entidad panameña; 0,6 si solo el medio es panameño | Todo TVN = 1,0 | TVN publica notas internacionales (American Idol, ébola en Kenia) que subían al top 5 |
| D10 | 2026-10-06 | El LLM solo redacta; puntaje, estado de evidencia y contexto los calcula código | LLM que prioriza | Reproducibilidad y resistencia a inyección: un texto no puede cambiar el puntaje |
| D11 | 2026-10-06 | Validador de citas en código, incluido control de cifras | Confiar en el formato JSON del LLM | El reto exige 100% de afirmaciones con cita; el formato no garantiza sustento |
| D12 | 2026-10-06 | Borrador con caché de LLM + plantilla determinista | Solo LLM | Demo sin internet (T10) y costo cero en evaluación |
| D13 | 2026-10-06 | Urgencia medida contra la fecha de corte del snapshot, no contra "ahora" | Reloj del sistema | Reproducibilidad: el mismo snapshot da el mismo ranking cualquier día |
| D14 | 2026-10-06 | Casos sintéticos (inyección, contradicciones, recirculada, agencia) en archivo aparte y rotulados | Alterar noticias reales | El reto pide identificar los casos alterados como sintéticos |
| D15 | 2026-10-06 | Normalizar espaciado de titulares GDELT en `processed/`; `raw/` intacto | Usar texto crudo | GDELT entrega "1 , 500" y "Panamá : …", que rompe la lectura de cifras |
| D16 | 2026-10-06 | IA generativa local: Hermes 3 3B vía Ollama por defecto | Claude u otra API de pago | Gratuito, sin clave y sin internet (T10). Pedido explícito del autor. Costo: más lento en CPU (~1 min) |
| D17 | 2026-10-06 | Borrador híbrido con modelos locales: hechos por código y redacción editorial por la IA | Borrador completo por la IA | Medido: el borrador completo tardó 228 s y truncó el JSON; el híbrido tarda ~73 s y pasa el validador |
| D18 | 2026-10-06 | En Consultar, la IA se pide con un botón; la respuesta inmediata es extractiva | Llamar siempre a la IA | En CPU tarda 45–75 s; la búsqueda no debe esperar. Lo ya generado sale de la caché |

## Cambios de pesos

Se mantienen los pesos iniciales del reto (30/25/20/15/10), versión `reglas-v1`. Cualquier cambio debe registrarse aquí con su justificación y subir la versión en `backend/app/scoring.py`.
