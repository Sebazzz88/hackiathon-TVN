# Presentación al jurado (10 minutos)

Estructura exigida: problema → solución → demo → IA y evidencias → resultados → límites → próximos pasos. Guion completo y respuestas a las preguntas dinámicas en `docs/11_PITCH.md`.

## 1 · Problema (1 min)
Un editor de TVN arranca el día con cientos de titulares. Muchos repiten la misma nota de agencia, otros son viejos y casi ninguno trae el dato oficial que permite ponerlos en contexto. **Que una noticia circule no significa que esté confirmada.**

## 2 · Solución (1 min)
Un copiloto que pasa de 875 titulares reales a 5 temas investigables. Muestra la evidencia que existe, lo que falta comprobar y propone un borrador con cita en cada frase. **Nada se publica solo**: decide una persona.

Datos públicos congelados:

| Fuente | Contenido |
|---|---|
| RSS de TVN | Solo metadatos |
| GDELT | Titulares de otros medios |
| Banco Mundial | Indicadores anuales |
| USGS | Sismos |

## 3 · Demo en vivo, sin internet (4 min)
Enlaces directos con la app encendida (`iniciar.ps1`):

1. `http://localhost:5173/#/datos`: reporte de calidad. Hay 875 noticias válidas, 152 de TVN.
2. `http://localhost:5173/#/agenda`: el top 5 con su puntaje y la barra de componentes.
3. `http://localhost:5173/#/ficha/EV-G226d8217c0/fuentes`: 6 titulares de S&P que equivalen a 4 fuentes independientes.
4. `http://localhost:5173/#/ficha/EV-G226d8217c0/resumen`: contexto del Banco Mundial con la advertencia "dato anual 2024, no de hoy".
5. Pestaña **Borrador** de esa ficha: cada frase lleva su tipo y su cita.
6. `http://localhost:5173/#/ficha/EV-T7bb199ba28/revision`: prioridad alta, pero el botón **aprobar está bloqueado** por evidencia insuficiente.
7. `http://localhost:5173/#/consulta?q=¿Cuál es la inflación de Panamá hoy?`: el sistema se abstiene.
8. `http://localhost:5173/#/ficha/SINT-S-INY-001/resumen`: una fuente intenta dar órdenes y recibe E = 0 sin ejecutar nada.

## 4 · IA y evidencias (2 min)
- **Embeddings multilingües locales (ONNX).** Clasifican en 6 temas, agrupan titulares del mismo hecho en varios idiomas y buscan por significado.
- **Procedencia léxica.** Una agencia replicada cuenta como una sola fuente.
- **Validador en código.** Ninguna frase sale sin cita válida ni con cifras que no estén en la fuente.
- **Baseline:** palabras clave y ranking por fecha.

## 5 · Resultados (1 min)
Tabla de `06_pruebas_y_metricas.md`.

| Métrica | Agente | Baseline |
|---|---|---|
| Abstención correcta | 20/20 | 2/20 |
| Respuestas sustentadas | 30/30 | 11/30 |
| Agrupación (F1) | 0,875 | 0,615 |
| Cobertura de citas | 100% | — |

En clasificación la IA **casi no mejora** al baseline: lo decimos tal cual.

## 6 · Límites (30 s)
- Solo titulares: "suficiente para borrador" no confirma nada.
- Las etiquetas están pendientes de revisión humana.
- Precision@5 está pendiente de que un editor elija su top 5.
- La detección de agencia e inyección se hace por patrones.

## 7 · Próximos pasos (30 s)
1. Que un editor de TVN valide el top 5 y los pesos.
2. Lectura autorizada de textos de TVN.
3. Más fuentes primarias, como comunicados oficiales y la Gaceta Oficial.
4. Medir el ahorro de tiempo con una tarea manual frente a una asistida.
