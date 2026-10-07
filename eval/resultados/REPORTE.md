# Resultados de evaluación — 2026-10-07T03:05:20+00:00

Conjunto: 60 consultas (40 dev / 20 reservadas). Propuestas por el asistente de IA (Claude) a partir de titulares y del snapshot; PENDIENTE revisión humana. Hasta entonces las métricas son preliminares.

| Métrica | Agente (IA) | Baseline | Nota |
|---|---|---|---|
| [dev] Respuestas sustentadas correctas | 20/20 (100%) | 6/20 (30%) | sin fallos |
| [dev] Contradicciones mostradas | 7/7 (100%) | 0/7 (0%) | sin fallos |
| [dev] Sin respuesta: abstención correcta | 7/7 (100%) | 1/7 (14%) | sin fallos |
| [dev] Adversariales rechazadas | 6/6 (100%) | 1/6 (17%) | sin fallos |
| [dev] Abstención correcta (sin respuesta + adversarial) | 13/13 (100%) | 2/13 (15%) | meta ≥ 80% |
| [dev] Abstención INCORRECTA en respondibles | 0/27 (0%) | 1/27 (4%) | menor es mejor |
| [reservado] Respuestas sustentadas correctas | 10/10 (100%) | 5/10 (50%) | sin fallos |
| [reservado] Contradicciones mostradas | 3/3 (100%) | 0/3 (0%) | sin fallos |
| [reservado] Sin respuesta: abstención correcta | 3/3 (100%) | 0/3 (0%) | sin fallos |
| [reservado] Adversariales rechazadas | 4/4 (100%) | 0/4 (0%) | sin fallos |
| [reservado] Abstención correcta (sin respuesta + adversarial) | 7/7 (100%) | 0/7 (0%) | meta ≥ 80% |
| [reservado] Abstención INCORRECTA en respondibles | 0/13 (0%) | 0/13 (0%) | menor es mejor |
| Cobertura de citas en borradores | 195/195 (100%) | — | 2 afirmaciones eliminadas por el validador; validez de sustento: PENDIENTE revisión humana (afirmaciones_para_revision.csv) |
| Clasificación temática macro-F1 [dev, n=100] | 0.568 | 0.547 | exactitud 83/100 (83%) vs 78/100 (78%) |
| Clasificación temática macro-F1 [test, n=50] | 0.44 | 0.395 | exactitud 39/50 (78%) vs 41/50 (82%) |
| Agrupación de eventos (pares, n=60) F1 | 0.875 | 0.615 | P 14/15 (93%) · R 14/17 (82%) |
| Precision@5 (exploratoria) | PENDIENTE | — | Falta eval/seleccion_editor.json (selección independiente de un editor). No se reporta Precision@5. |
| Tiempo por consulta (mediana / p95) | 0.004 s / 0.011 s | — | meta mediana ≤ 15 s; pipeline completo 5.5 s |
| Tiempo por borrador (mediana / p95) | 0.002 s / 0.003 s | — | 0 USD en esta ejecución (LLM_OFFLINE=1: plantilla determinista o caché). |

## Top 5 del agente vs baseline por fecha

1. Canal de Panamá: Suspensión temporal de operaciones de potabilizadora de Miraflores este miércoles (`EV-T7bb199ba28`)
2. Sinaproc extiende vigilancia por lluvias, tormentas y vientos hasta el viernes (`EV-Ta0993c4b63`)
3. Panamá reforzará su presencia marítima en Vietnam con nueva oficina de servicio técnico de la AMP en Ho Chi Minh (`EV-Te569818877`)
4. Sismo de magnitud 3.3 sorprende durante la madrugada: ocurrió al noroeste de Chepo (`EV-G1454ad17a8`)
5. Moody: Cobre Panamá puede incidir en el grado de inversión (`EV-Gb01bc434a8`)

Baseline (más reciente primero):

1. Príncipes de Gales: los nombres que usan en el colegio sus hijos (`EV-T8345efcf73`)
2. Panamá mantiene vigilancia epidemiológica ante caso sospechoso de peste neumónica en Rusia (`EV-Teb754d221e`)
3. Canal de Panamá: Suspensión temporal de operaciones de potabilizadora de Miraflores este miércoles (`EV-T7bb199ba28`)
4. Sinaproc extiende vigilancia por lluvias, tormentas y vientos hasta el viernes (`EV-Ta0993c4b63`)
5. Agroferias del IMA: Conozca dónde se realizarán este miércoles (`EV-T0eeb2a8a38`)

## Errores de clasificación del agente (test)

- «Presentan a las obras ganadoras de Documental Panamá» humano=otros agente=turismo
- «Contenido Exclusivo: Coclé, se seca el campo» humano=eventos_naturales agente=otros
- «PASE-U: compras con la billetera de Caja de Ahorros superan los $45 millones desde junio» humano=economia agente=otros
- «2,643 horas: la carga invisible de la burocracia en Panamá» humano=economia agente=otros
- «S & P Global ratifica grado de inversión de Panamá» humano=economia agente=otros
- «Caso PPC: el Ministerio Público no avanza, porque espera la ampliación de la auditoría de la Contraloría» humano=otros agente=regulacion
- «Campaña contra el cáncer en Panamá: estas son las actividades programadas para octubre» humano=servicios_publicos agente=otros
- «Tu Banco, tu Istmo: Banistmo presenta nueva identidad como parte del Grupo Financiero BSC» humano=economia agente=otros
- «Multitudinario desfile de carretas en Guararé; TVN Media se tomó el Festival de la Mejorana» humano=otros agente=turismo
- «Σούπερ Ελ Νίνιο χωρίς προηγούμενο εδώ και 1.000 χρόνια – Οι φόβοι για όσα έρχονται» humano=eventos_naturales agente=otros
- «TVN Media y el Teatro Nacional sellan alianza para promover la cultura panameña» humano=otros agente=turismo
