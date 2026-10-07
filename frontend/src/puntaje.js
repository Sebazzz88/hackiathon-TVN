// Puntaje de atención del reto, replicado en el navegador SOLO para la vista "¿qué pasaría si…?".
// El ranking oficial lo calcula el backend (backend/app/scoring.py, reglas-v1). Esto no guarda nada.
export const PESOS_RETO = { R: 30, I: 25, U: 20, N: 15, E: 10 };
export const REGLAS = "reglas-v1";

/** Normaliza pesos a suma 100 (si todos son 0, vuelve a los del reto). */
export function normalizar(pesos) {
  const total = Object.values(pesos).reduce((a, b) => a + Math.max(0, Number(b) || 0), 0);
  if (!total) return { ...PESOS_RETO };
  return Object.fromEntries(Object.entries(pesos).map(([k, v]) => [k, (Math.max(0, Number(v) || 0) * 100) / total]));
}

/** P = Σ peso·componente (componentes 0–1), redondeado a 2 decimales como en el backend. */
export function puntajeCon(c, pesos = PESOS_RETO) {
  const p = normalizar(pesos);
  return Math.round(Object.keys(PESOS_RETO).reduce((s, k) => s + p[k] * Math.min(1, Math.max(0, c[k] || 0)), 0) * 100) / 100;
}

export const banda = (p) => (p < 40 ? "bajo" : p < 70 ? "medio" : "alto");

/** Orden del reto: mayor puntaje; empate: mayor urgencia; luego ID. */
export function rankear(items, pesos = PESOS_RETO) {
  return items
    .map((f) => ({ ...f, puntaje_sim: puntajeCon(f.componentes, pesos) }))
    .sort((a, b) => b.puntaje_sim - a.puntaje_sim || b.componentes.U - a.componentes.U || (a.id_caso < b.id_caso ? -1 : 1));
}

/** Ranking simulado con la posición original y el cambio (positivo = sube). */
export function simular(items, pesos) {
  const base = new Map(rankear(items, PESOS_RETO).map((f, i) => [f.id_caso, i + 1]));
  return rankear(items, pesos).map((f, i) => ({ ...f, pos: i + 1, pos_base: base.get(f.id_caso), cambio: base.get(f.id_caso) - (i + 1) }));
}

/** Aporte en puntos de cada componente con los pesos dados. */
export const aportes = (c, pesos = PESOS_RETO) => {
  const p = normalizar(pesos);
  return Object.fromEntries(Object.keys(PESOS_RETO).map((k) => [k, Math.round(p[k] * (c[k] || 0) * 10) / 10]));
};
