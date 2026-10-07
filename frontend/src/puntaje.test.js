import assert from "node:assert/strict";
import { test } from "node:test";
import { PESOS_RETO, aportes, banda, normalizar, puntajeCon, rankear, simular } from "./puntaje.js";

const f = (id, R, I, U, N, E) => ({ id_caso: id, componentes: { R, I, U, N, E } });

test("con los pesos del reto da lo mismo que el backend (P = 30R+25I+20U+15N+10E)", () => {
  assert.equal(puntajeCon({ R: 1, I: 1, U: 1, N: 1, E: 1 }), 100);
  assert.equal(puntajeCon({ R: 0.99, I: 0.91, U: 0.01, N: 0.29, E: 1 }), 0.99 * 30 + 0.91 * 25 + 0.01 * 20 + 0.29 * 15 + 10);
  assert.deepEqual([banda(39.99), banda(40), banda(70)], ["bajo", "medio", "alto"]);
});

test("los pesos se normalizan a 100; todo en cero vuelve a los del reto", () => {
  const n = normalizar({ R: 1, I: 1, U: 1, N: 1, E: 1 });
  assert.equal(Math.round(Object.values(n).reduce((a, b) => a + b, 0)), 100);
  assert.deepEqual(normalizar({ R: 0, I: 0, U: 0, N: 0, E: 0 }), PESOS_RETO);
  assert.equal(puntajeCon({ R: 1, I: 0, U: 0, N: 0, E: 0 }, { R: 60, I: 50, U: 40, N: 30, E: 20 }), 30);  // 60/200
});

test("desempate del reto: mayor urgencia y luego ID", () => {
  const r = rankear([f("B", 1, 0, 0, 0, 0), f("A", 1, 0, 0, 0, 0), f("C", 0.5, 0, 1, 0, 0)], { R: 50, I: 0, U: 25, N: 0, E: 0 });
  assert.deepEqual(r.map((x) => x.id_caso), ["C", "A", "B"]);  // C: 50; A y B: 66.7 empatan -> U igual -> ID
});

test("simular dice cuánto sube o baja cada tema al cambiar un peso", () => {
  const items = [f("URGENTE", 0.5, 0.5, 1, 0.5, 0.1), f("RESPALDADO", 0.5, 0.5, 0.1, 0.5, 1)];
  const base = simular(items, PESOS_RETO);
  assert.equal(base[0].id_caso, "URGENTE");
  const evidencia = simular(items, { R: 30, I: 25, U: 5, N: 15, E: 60 });
  assert.deepEqual(evidencia.map((x) => [x.id_caso, x.pos, x.pos_base, x.cambio]), [["RESPALDADO", 1, 2, 1], ["URGENTE", 2, 1, -1]]);
});

test("aportes por componente suman el puntaje", () => {
  const c = { R: 0.9, I: 0.8, U: 0.3, N: 0.6, E: 0.5 };
  const a = aportes(c);
  assert.ok(Math.abs(Object.values(a).reduce((x, y) => x + y, 0) - puntajeCon(c)) < 0.3);
});
