# Producto

> Usuario, propuesta de valor, flujo

**Modalidad:** TVN editorial (principal). La modalidad bancaria no se implementa.

**Usuario:** editor/a o periodista de la mesa de TVN que planifica la agenda del día.

**Propuesta de valor:** pasar de cientos de titulares dispersos a cinco temas investigables, con la evidencia que existe, lo que falta comprobar y un borrador con cita por afirmación. Reduce el tiempo de búsqueda y verificación; no produce más texto ni publica nada.

## Flujo en la interfaz (http://localhost:5173)

1. **Reporte de calidad:** registros válidos, con error, de TVN, celdas del Banco Mundial, sismos USGS y cobertura.
2. **Bandeja priorizada:** top 5 (o 10/30) con puntaje 0–100, banda, barra por componente R, I, U, N, E, tema, titulares agrupados, procedencias independientes y estado de evidencia. Casos sintéticos en un filtro aparte.
3. **Ficha:** qué se reporta, quién lo reporta, qué está respaldado (con id y campo), contexto oficial con año y unidad, versiones incompatibles, qué falta comprobar, acción recomendada, puntaje desglosado con justificación y tabla de titulares en hora de Panamá.
4. **Borrador:** título, enfoque de interés público, brief ≤ 250 palabras, 3 preguntas, verificaciones pendientes, guion 45–60 s y copy ≤ 80 palabras. Cada afirmación muestra su tipo y sus citas. Se listan las afirmaciones eliminadas por el validador.
5. **Revisión humana:** 5 estados, nombre de la persona revisora obligatorio y comentario. Historial visible. Aprobar no publica; con evidencia insuficiente no se puede aprobar.
6. **Consulta en español:** indicadores con país, año y unidad; noticias con procedencias; abstención explícita.
7. **Panel de evaluación:** métricas del agente frente al baseline.

## Criterios de éxito

| Criterio | Medición |
|---|---|
| Top 5 útil para la agenda | Precision@5 frente a un editor (PENDIENTE: requiere selección independiente) |
| Ninguna afirmación sin cita | Cobertura de citas 100% (validador en código) |
| Abstención cuando no hay evidencia | ≥ 80% en consultas sin respuesta y adversariales |
| Rapidez | Mediana ≤ 15 s por consulta |
