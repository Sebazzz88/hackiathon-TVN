// Utilidades compartidas: API, formatos (hora de Panamá) y catálogos de etiquetas.

const esperar = (ms) => new Promise((r) => setTimeout(r, ms));

/** Error de red/servidor con un mensaje que dice qué hacer. `transitorio` = vale la pena reintentar. */
export class ApiError extends Error {
  constructor(mensaje, { estado = 0, transitorio = false } = {}) {
    super(mensaje);
    this.estado = estado;
    this.transitorio = transitorio;
  }
}

/** Llama al backend. Admite `signal` (para cancelar respuestas viejas) y reintenta UNA vez los GET que fallan por
 *  red o error 5xx (el backend puede estar ocupado con la IA). Los 4xx (409, 422...) no se reintentan: son respuestas. */
export async function api(path, method = "GET", body, signal) {
  const url = path.startsWith("/health") ? path : "/api" + path;
  for (let intento = 0; ; intento++) {
    try {
      const r = await fetch(url, {
        method, signal, headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined,
      });
      const d = await r.json().catch(() => ({}));
      if (r.ok) return d;
      const detalle = typeof d.detail === "string" ? d.detail : null;
      throw new ApiError(detalle || (r.status >= 500
        ? "El servidor tuvo un problema. Reintenta; si persiste, revisa la ventana del backend."
        : `No se pudo completar la solicitud (${r.status}).`), { estado: r.status, transitorio: r.status >= 500 });
    } catch (e) {
      if (e.name === "AbortError") throw e;  // cancelada a propósito: no es un error
      const err = e instanceof ApiError ? e : new ApiError(
        "No hay conexión con el backend. Enciéndelo (run_demo.ps1 o iniciar.ps1) y vuelve a intentarlo.", { transitorio: true });
      if (method === "GET" && err.transitorio && intento === 0) { await esperar(700); continue; }
      throw err;
    }
  }
}

// Borradores que se están generando (la IA local tarda ~1 min). Viven fuera de los componentes: si cambias de ficha
// o de pestaña mientras tanto, al volver se ve "Generando…" y no se lanza una segunda generación.
const enCurso = new Map();
export const generando = (id) => enCurso.has(id);
export function generarBorrador(id) {
  if (!enCurso.has(id)) enCurso.set(id, api(`/fichas/${id}/draft`, "POST").finally(() => enCurso.delete(id)));
  return enCurso.get(id);
}

/** true si el error es una cancelación intencional (se ignora). */
export const cancelado = (e) => e?.name === "AbortError";

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

/** "6 notas · 3 procedencias independientes" (mismo dominio o misma agencia = 1 procedencia). */
export function textoProcedencia(f) {
  const notas = f.fuentes_totales || f.registros || 0;
  const proc = f.procedencias_independientes || f.fuentes_independientes || 0;
  return `${notas} nota${notas === 1 ? "" : "s"} · ${proc} procedencia${proc === 1 ? "" : "s"} independiente${proc === 1 ? "" : "s"}`;
}

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
