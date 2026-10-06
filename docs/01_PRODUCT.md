# Producto

> Usuario, propuesta de valor, flujo

**Modalidad:** TVN editorial (principal). La modalidad bancaria no se implementa.

**Usuario:** editor/a o periodista de la mesa de TVN que planifica la agenda del día.

**Propuesta de valor:** pasar de cientos de titulares dispersos a cinco temas investigables, con la evidencia que existe, lo que falta comprobar y un borrador con cita por afirmación. Reduce el tiempo de búsqueda y verificación; no produce más texto ni publica nada.

## Flujo en la interfaz (http://localhost:5173)

Barra superior con cuatro pestañas y la fecha de corte del snapshot en hora de Panamá.

1. **Agenda.** Top 5, 10 o 30 temas con puntaje 0–100 (rojo = prioridad alta), tema, antigüedad, estado de evidencia, fuentes independientes y barra de componentes R, I, U, N, E. Los casos de prueba sintéticos están en una lista aparte.
2. **Ficha** (sub-pestañas de la agenda):
   - *Ficha:* qué se reporta, quién lo reporta, qué está respaldado (con id y campo), contexto oficial con año y unidad, versiones incompatibles lado a lado, qué falta comprobar y acción recomendada.
   - *Fuentes:* titulares agrupados por procedencia ("3 titulares = 1 fuente"), con fecha de publicación o de detección.
   - *Puntaje:* fórmula, barras por componente, aporte de cada uno y justificación.
   - *Borrador:* título, enfoque, brief ≤ 250 palabras, 3 preguntas, pendientes, guion 45–60 s y copy ≤ 80 palabras. Cada afirmación muestra tipo y cita, y se listan las eliminadas por el validador.
   - *Revisión:* 5 estados, persona revisora obligatoria, comentario e historial. Aprobar no publica; con evidencia insuficiente el botón está bloqueado.
3. **Consultar.** Preguntas en español con ejemplos (respuesta, abstención, contradicción, inyección). Los eventos recuperados abren su ficha.
4. **Datos.** Reporte de calidad, catálogo con SHA-256 y límites de cobertura.
5. **Evaluación.** Métricas del agente frente al baseline y top 5 comparado.

Cada vista tiene un enlace directo (`#/ficha/<id>/<sección>`, `#/consulta?q=…`, `#/datos`, `#/evaluacion`) para usarlo en el pitch o en Notion.

## Criterios de éxito

| Criterio | Medición |
|---|---|
| Top 5 útil para la agenda | Precision@5 frente a un editor (PENDIENTE: requiere selección independiente) |
| Ninguna afirmación sin cita | Cobertura de citas 100% (validador en código) |
| Abstención cuando no hay evidencia | ≥ 80% en consultas sin respuesta y adversariales |
| Rapidez | Mediana ≤ 15 s por consulta |
