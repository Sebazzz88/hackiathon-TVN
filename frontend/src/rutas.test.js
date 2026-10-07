// Pruebas de rutas sin dependencias: `npm test` (usa el runner de Node).
import assert from "node:assert/strict";
import { test } from "node:test";
import { construir, fichaVigente, normalizarN, parsear } from "./rutas.js";

test("agenda por defecto: 5 reales", () => {
  assert.deepEqual(parsear("").n, 5);
  assert.equal(parsear("#/agenda").sint, false);
  assert.equal(construir({}), "#/agenda");
});

test("cambiar 5 -> 10 -> 5 -> 30 siempre queda en el último valor", () => {
  let r = parsear("#/agenda");
  for (const n of [10, 5, 30, 5]) r = parsear(construir({ ...r, n }));
  assert.equal(r.n, 5);
  assert.equal(parsear(construir({ n: 30 })).n, 30);
  assert.equal(parsear("#/agenda?n=10").n, 10);
});

test("valores inválidos vuelven al valor seguro (nada de 500 por n=-3 o n=abc)", () => {
  for (const malo of ["abc", "-3", "0", "1001", "2.5", "", "NaN", "1e9"]) assert.equal(normalizarN(malo), 5, malo);
  assert.equal(parsear("#/agenda?n=abc").n, 5);
});

test("número personalizado y Máx se conservan en la URL", () => {
  assert.equal(parsear(construir({ n: 12 })).n, 12);
  assert.equal(parsear("#/agenda?n=max").n, "max");
  assert.equal(parsear(construir({ n: "max", sint: true })).n, "max");
  assert.equal(parsear(construir({ n: 1000 })).n, 1000);
  assert.equal(normalizarN("37"), 37);
});

test("casos de prueba se conservan al cambiar el tamaño y no dependen de la ficha", () => {
  const r = parsear("#/agenda?n=10&p=1");
  assert.equal(r.sint, true);
  assert.equal(parsear(construir({ ...r, n: 5 })).sint, true);
  assert.equal(parsear(construir({ ...r, sint: false })).sint, false);
});

test("ficha dentro de una lista conserva tamaño y casos de prueba", () => {
  const h = construir({ ficha: "SINT-S-CON-001", seccion: "borrador", n: 10, sint: true });
  assert.equal(h, "#/ficha/SINT-S-CON-001/borrador?n=10&p=1");
  const r = parsear(h);
  assert.deepEqual([r.ficha, r.seccion, r.n, r.sint, r.vista], ["SINT-S-CON-001", "borrador", 10, true, "agenda"]);
});

test("enlaces antiguos siguen funcionando y secciones inválidas caen en 'resumen'", () => {
  assert.equal(parsear("#/ficha/EV-G226d8217c0/fuentes").seccion, "fuentes");
  assert.equal(parsear("#/ficha/EV-X/inexistente").seccion, "resumen");
  assert.equal(parsear("#/ficha/EV-X").ficha, "EV-X");
});

test("consulta conserva la pregunta con acentos, signos y &", () => {
  const q = "¿Qué dijo S&P sobre el grado de inversión?";
  assert.equal(parsear(construir({ vista: "consulta", q })).q, q);
});

test("ID con caracteres especiales se codifica y decodifica", () => {
  const r = parsear(construir({ ficha: "WB:PAN:FP.CPI.TOTL.ZG:2023" }));
  assert.equal(r.ficha, "WB:PAN:FP.CPI.TOTL.ZG:2023");
});

test("una respuesta tardía de otra ficha no reemplaza la que está abierta", () => {
  assert.equal(fichaVigente({ id_caso: "A" }, "A"), true);
  assert.equal(fichaVigente({ id_caso: "A" }, "B"), false);   // el borrador de A llegó cuando ya se abrió B
  assert.equal(fichaVigente(null, "B"), false);
});
