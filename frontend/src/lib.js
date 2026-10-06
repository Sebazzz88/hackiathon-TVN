// Utilidades compartidas: API, formatos (hora de Panamá) y catálogos de etiquetas.

export async function api(path, method = "GET", body) {
  const url = path.startsWith("/health") ? path : "/api" + path;
  const r = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(typeof d.detail === "string" ? d.detail : `Error ${r.status}`);
  return d;
}

export const TEMAS = {
  economia: "Economía",
  logistica_canal: "Canal y logística",
  turismo: "Turismo",
  servicios_publicos: "Servicios públicos",
  eventos_naturales: "Eventos naturales",
  regulacion: "Regulación",
  otros: "Otros",
};

export const COMPONENTES = [
  ["R", "Relevancia", 30],
  ["I", "Impacto", 25],
  ["U", "Urgencia", 20],
  ["N", "Novedad", 15],
  ["E", "Evidencia", 10],
];

export const ESTADOS = [
  ["nuevo", "Nuevo"],
  ["en_revision", "En revisión"],
  ["requiere_evidencia", "Requiere evidencia"],
  ["aprobado_como_borrador", "Aprobado como borrador"],
  ["descartado", "Descartado"],
];
export const estadoTxt = (e) => (ESTADOS.find(([k]) => k === e) || [e, e])[1];

export const EVIDENCIA = {
  insuficiente: "Evidencia insuficiente",
  parcial: "Evidencia parcial",
  suficiente_para_borrador: "Suficiente para borrador",
};

export const TIPOS = { hecho: "Hecho", declaracion: "Declaración", inferencia: "Inferencia", hipotesis: "Hipótesis" };

const fmt = new Intl.DateTimeFormat("es-PA", {
  timeZone: "America/Panama", day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
});
const fmtFecha = new Intl.DateTimeFormat("es-PA", { timeZone: "America/Panama", day: "2-digit", month: "short", year: "numeric" });

/** Fecha en hora de Panamá (UTC−5). */
export const horaPA = (s) => (s ? fmt.format(new Date(s)) : "—");
export const fechaPA = (s) => (s ? fmtFecha.format(new Date(s)) : "—");

/** Antigüedad relativa respecto de la fecha de corte del snapshot (no del reloj del equipo). */
export function hace(s, corte) {
  if (!s) return "sin fecha";
  const h = (new Date(corte || Date.now()) - new Date(s)) / 36e5;
  if (h < 1) return "hace minutos";
  if (h < 24) return `hace ${Math.round(h)} h`;
  const d = Math.round(h / 24);
  return d < 60 ? `hace ${d} d` : `hace ${Math.round(d / 30)} meses`;
}
