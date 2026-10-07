// Mini bus para abrir el registro fuente de una cita desde cualquier vista sin pasar props por todos lados.
const oyentes = new Set();

/** Abre el panel con el registro fuente de la evidencia `id`, resaltando el `campo` citado. */
export const abrirEvidencia = (id, campo = "") => oyentes.forEach((f) => f({ id, campo }));

/** Para el panel: se suscribe y devuelve la función para cancelar la suscripción. */
export const suscribirEvidencia = (f) => { oyentes.add(f); return () => oyentes.delete(f); };

/** Etiquetas legibles de los campos de cada tipo de evidencia. La fecha de publicación NUNCA se mezcla con la de detección. */
export const ETIQUETAS = {
  titulo: "Titular", medio: "Medio", url: "URL", idioma: "Idioma", origen: "Origen",
  fecha_publicacion: "Fecha de publicación", fecha_deteccion: "Fecha de detección (GDELT)",
  pais: "País", indicador: "Indicador", anio: "Año", valor: "Valor", unidad: "Unidad", licencia: "Licencia",
  fecha_extraccion: "Fecha de extracción", magnitude: "Magnitud", place: "Lugar", time: "Hora del sismo (UTC)",
  depth: "Profundidad (km)", latitude: "Latitud", longitude: "Longitud", status: "Estado",
  id_caso: "Evento", metodo: "Método",
};
export const TIPOS_EV = { noticia: "Noticia (titular y metadatos)", indicador: "Indicador oficial", sismo: "Evento sísmico oficial", agrupacion: "Dato del sistema" };
