// Rutas por hash: la URL es la ÚNICA fuente de verdad de la navegación (vista, ficha, tamaño de lista, casos de prueba).
// Así los botones, el botón "atrás" y los enlaces directos nunca quedan desincronizados.
//   #/agenda?n=10&p=1            lista de 10 casos de prueba
//   #/ficha/<id>/<seccion>?n=30  ficha abierta dentro de una lista de 30
//   #/consulta?q=<pregunta>      #/datos      #/evaluacion
export const VISTAS = ["agenda", "consulta", "datos", "evaluacion"];
export const TAMANOS = [5, 10, 30];       // atajos de la interfaz
export const N_MAX = 1000;                 // tope del backend; "max" pide todo
export const SECCIONES = ["resumen", "fuentes", "puntaje", "borrador", "revision"];

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
  const base = { n: normalizarN(p.get("n")), sint: p.get("p") === "1", q: p.get("q") || "" };
  if (partes[0] === "ficha" && partes[1]) {
    return { ...base, vista: "agenda", ficha: partes[1], seccion: SECCIONES.includes(partes[2]) ? partes[2] : "resumen" };
  }
  return { ...base, vista: VISTAS.includes(partes[0]) ? partes[0] : "agenda", ficha: null, seccion: "resumen" };
}

export function construir({ vista = "agenda", ficha = null, seccion = "resumen", n = 5, sint = false, q = "" } = {}) {
  const params = new URLSearchParams();
  if (vista === "consulta") {
    if (q) params.set("q", q);
  } else if (vista === "agenda") {
    const nn = normalizarN(n);
    if (nn !== 5) params.set("n", String(nn));
    if (sint) params.set("p", "1");
  }
  const qs = params.toString() ? `?${params}` : "";
  if (vista === "agenda" && ficha) return `#/ficha/${encodeURIComponent(ficha)}/${seccion}${qs}`;
  return `#/${vista}${qs}`;
}
