// UX editorial (punto 9): fechas en hora de Panamá sin mezclar publicación y detección, y contraste AA de la paleta.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fechasNota, horaPA } from "./lib.js";

test("hora de Panamá (UTC−5, sin horario de verano)", () => {
  assert.match(horaPA("2026-10-07T03:10:00Z"), /06.*22:10|06.*10:10/);  // 03:10 UTC = 22:10 del día anterior en Panamá
  assert.equal(horaPA(null), "—");
});

test("publicación y detección se muestran por separado", () => {
  assert.match(fechasNota({ fecha_publicacion: "2026-10-05T15:00:00Z" }), /^publicado /);
  const gdelt = fechasNota({ fecha_publicacion: "", fecha_deteccion: "2026-10-05T15:00:00Z" });
  assert.match(gdelt, /^sin fecha de publicación · detectado /);
  const ambas = fechasNota({ fecha_publicacion: "2023-06-15T12:00:00Z", fecha_deteccion: "2026-10-05T15:00:00Z" });
  assert.match(ambas, /publicado .*2023|publicado .* · detectado /);
  assert.ok(ambas.includes(" · detectado "));
});

// Contraste WCAG 2.1 de los colores de texto sobre sus fondos, en modo claro y oscuro.
const css = readFileSync(new URL("./style.css", import.meta.url), "utf8");
const bloque = (re) => Object.fromEntries([...css.match(re)[1].matchAll(/--([\w-]+):\s*(#[0-9a-f]{6})/gi)].map((m) => [m[1], m[2]]));
const claro = bloque(/:root\s*\{([^}]*)\}/);
const oscuro = { ...claro, ...bloque(/prefers-color-scheme:\s*dark\)\s*\{\s*:root\s*\{([^}]*)\}/) };
const lum = (h) => {
  const c = [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16) / 255).map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
};
const contraste = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };

for (const [modo, t] of [["claro", claro], ["oscuro", oscuro]]) {
  test(`contraste AA (≥ 4.5:1) en modo ${modo}`, () => {
    const pares = [["tinta", "bg"], ["tinta", "panel"], ["suave", "bg"], ["suave", "panel"], ["ok", "panel"], ["mal", "panel"],
      ["medio", "panel"], ["azul", "panel"], ["barra-txt", "barra"]];
    for (const [f, b] of pares) {
      const r = contraste(t[f], t[b]);
      assert.ok(r >= 4.5, `${f} sobre ${b}: ${r.toFixed(2)}:1`);
    }
  });
}
