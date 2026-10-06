# Problema

> Reto oficial de TVN, usuario, restricciones

Resumen completo en [RETO.md](RETO.md); fuente: `docs/reto_TVN.pdf`.

**Problema.** Una mesa editorial revisa fuentes dispersas, elimina duplicados y ubica hechos en contexto bajo presión de tiempo. La circulación de una noticia no equivale a su confirmación: varios medios pueden repetir una misma fuente o agencia.

**Usuario.** Editor/a y periodista de TVN.

**Restricciones del reto que condicionan el diseño**

- Solo datos públicos reproducibles. De TVN se usan únicamente metadatos del RSS (título, URL, fecha).
- Toda afirmación debe vincularse a fuente, fecha y alcance. Prohibido inventar cifras, citas, entrevistas o causas.
- Si solo hay titular y metadatos, la salida lo dice: "basado únicamente en titular/metadatos".
- Puntaje de atención P = 30R + 25I + 20U + 15N + 10E, separado del estado de evidencia.
- Nada se publica automáticamente; la persona revisora decide.
- Debe funcionar sin internet durante la demo.

**Fuera de alcance.** Rating o audiencia, detección definitiva de noticias falsas, datos personales, contenido detrás de paywalls, producción audiovisual y la modalidad bancaria.
