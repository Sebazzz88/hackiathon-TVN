// api(): una cancelación durante la lectura de la respuesta debe propagarse, nunca convertirse en datos vacíos.
import { test } from "node:test";
import assert from "node:assert/strict";
import { api, cancelado } from "./lib.js";

const respuesta = (json, ok = true, status = 200) => ({ ok, status, json });

test("cancelada mientras se lee el cuerpo → AbortError (antes devolvía {})", async () => {
  globalThis.fetch = async () => respuesta(() => Promise.reject(new DOMException("aborted", "AbortError")));
  await assert.rejects(api("/inbox?limit=5"), (e) => cancelado(e));
});

test("señal cancelada después de leer → AbortError, la vista no recibe una respuesta vieja", async () => {
  const ac = new AbortController();
  globalThis.fetch = async () => respuesta(async () => { ac.abort(); return { items: [], total: 0 }; });
  await assert.rejects(api("/inbox?limit=5", "GET", undefined, ac.signal), (e) => cancelado(e));
});

test("cuerpo ilegible con 200 → error con mensaje que dice qué hacer", async () => {
  globalThis.fetch = async () => respuesta(() => Promise.reject(new SyntaxError("JSON")));
  await assert.rejects(api("/fichas/X", "POST"), /Reintenta/);
});

test("respuesta normal → datos", async () => {
  globalThis.fetch = async () => respuesta(async () => ({ items: [1], total: 1 }));
  assert.deepEqual(await api("/inbox?limit=1"), { items: [1], total: 1 });
});
