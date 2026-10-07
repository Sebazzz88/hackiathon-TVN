// Rutas por hash: la URL es la ÚNICA fuente de verdad de la navegación (vista, ficha, tamaño de lista, casos de prueba).
// Así los botones, el botón "atrás" y los enlaces directos nunca quedan desincronizados.
//   #/agenda?n=10&p=1            lista de 10 casos de prueba
//   #/ficha/<id>/<seccion>?n=30  ficha abierta dentro de una lista de 30
//   #/consulta?q=<pregunta>      #/datos      #/evaluacion
export const VISTAS = ["agenda", "consulta", "datos", "evaluacion", "jurado"];
export const TAMANOS = [5, 10, 30];       // atajos de la interfaz
export const N_MAX = 1000;                 // tope del backend; "max" pide todo
export const SECCIONES = ["resumen", "fuentes", "puntaje", "borrador", "revision"];
export const TEMAS_IDS = ["economia", "logistica_canal", "turismo", "servicios_publicos", "eventos_naturales", "regulacion", "otros"];
export const VENTANAS = [1, 7, 30];

/** días válidos = entero 1..90; cualquier otra cosa = sin ventana (null). */
export function normalizarDias(v) {
  const d = Number(v);
  return v != null && v !== "" && Number.isInteger(d) && d >= 1 && d <= 90 ? d : null;
}

/** n válido = entero 1..1000 o "max". Cualquier otra cosa vuelve a 5 (nunca llega un valor raro al backend). */
export function normalizarN(v) {
  if (v === "max") return "max";
  const n = Number(v);
  return Number.isInteger(n) && n >= 1 && n <= N_MAX ? n : 5;
}

/** Una respuesta tardía (p. ej. un borrador de 1 min) solo puede reemplazar la ficha abierta si ES esa ficha. */
export const fichaVigente = (ficha, idActivo) => !!ficha && ficha.id_caso === idActivo;

export function parsear(hash) {
  const [ruta, qs] = String(hash || "").replace(/^#\/?/, "").split("?");
  const partes = ruta.split("/").filter(Boolean).map((x) => { try { return decodeURIComponent(x); } catch { return x; } });
  const p = new URLSearchParams(qs || "");
  const base = {
    n: normalizarN(p.get("n")), sint: p.get("p") === "1", q: p.get("q") || "",
    tema: TEMAS_IDS.includes(p.get("t")) ? p.get("t") : null, dias: normalizarDias(p.get("d")), c: p.get("c") || "",
  };
  if (partes[0] === "ficha" && partes[1]) {
    return { ...base, vista: "agenda", ficha: partes[1], seccion: SECCIONES.includes(partes[2]) ? partes[2] : "resumen" };
  }
  return { ...base, vista: VISTAS.includes(partes[0]) ? partes[0] : "agenda", ficha: null, seccion: "resumen" };
}

export function construir({ vista = "agenda", ficha = null, seccion = "resumen", n = 5, sint = false, q = "", tema = null, dias = null, c = "" } = {}) {
  const params = new URLSearchParams();
  if (vista === "consulta") {
    if (q) params.set("q", q);
  } else if (vista === "agenda") {
    const nn = normalizarN(n);
    if (nn !== 5) params.set("n", String(nn));
    if (sint) params.set("p", "1");
    if (TEMAS_IDS.includes(tema)) params.set("t", tema);
    if (normalizarDias(dias)) params.set("d", String(dias));
    if (c && (tema || dias)) params.set("c", c);
  }
  const qs = params.toString() ? `?${params}` : "";
  if (vista === "agenda" && ficha) return `#/ficha/${encodeURIComponent(ficha)}/${seccion}${qs}`;
  return `#/${vista}${qs}`;
}
