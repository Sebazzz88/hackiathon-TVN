// Arnés común de las pruebas de extremo a extremo: abre Edge o Chrome SIN ventana (headless), habla con él por el
// protocolo de depuración (CDP, sin dependencias) y lleva la cuenta de comprobaciones, errores 5xx y excepciones.
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

export const URL_APP = process.env.APP_URL || "http://localhost:5173";
const NAVEGADORES = [
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
];

export const dormir = (ms) => new Promise((r) => setTimeout(r, ms));

/** Abre el navegador sin ventana y devuelve { ev, esperarHasta, enviar, errores, cerrar }. */
export async function abrirNavegador(puerto) {
  const exe = NAVEGADORES.find(existsSync);
  if (!exe) { console.error("No encontré Edge ni Chrome."); process.exit(2); }
  const proc = spawn(exe, ["--headless=new", `--remote-debugging-port=${puerto}`, "--disable-gpu", "--window-size=1440,1000",
    `--user-data-dir=${mkdtempSync(join(tmpdir(), "tvn-e2e-"))}`, "about:blank"], { stdio: "ignore" });
  let ws = null;
  for (let i = 0; i < 40 && !ws; i++) {
    try {
      const p = (await (await fetch(`http://localhost:${puerto}/json`)).json()).find((x) => x.type === "page");
      if (p) { const w = new WebSocket(p.webSocketDebuggerUrl); await new Promise((ok, no) => { w.onopen = ok; w.onerror = no; }); ws = w; }
    } catch { /* aún arrancando */ }
    if (!ws) await dormir(250);
  }
  if (!ws) { proc.kill(); throw new Error("No pude conectar con el navegador"); }

  let id = 0;
  const pendientes = new Map();
  const errores = { consola: [], red: [] };
  ws.onmessage = (m) => {
    const d = JSON.parse(m.data);
    if (d.id && pendientes.has(d.id)) { pendientes.get(d.id)(d); pendientes.delete(d.id); }
    else if (d.method === "Runtime.exceptionThrown") {
      errores.consola.push(d.params.exceptionDetails.text + " " + (d.params.exceptionDetails.exception?.description || ""));
    } else if (d.method === "Runtime.consoleAPICalled" && d.params.type === "error" && d.params.args.some((x) => x.subtype === "error")) {
      // Errores capturados por la interfaz (p. ej. la vista que se rompe y muestra "Esta vista tuvo un problema").
      errores.consola.push("console.error: " + d.params.args.map((x) => x.value ?? x.description ?? "").join(" ").slice(0, 3000));
    } else if (d.method === "Network.responseReceived" && d.params.response.status >= 500) {
      errores.red.push(`${d.params.response.status} ${d.params.response.url}`);
    }
  };
  const enviar = (method, params = {}) => new Promise((ok) => { const n = ++id; pendientes.set(n, ok); ws.send(JSON.stringify({ id: n, method, params })); });
  const ev = async (js) => (await enviar("Runtime.evaluate", { expression: js, returnByValue: true, awaitPromise: true })).result?.result?.value;
  /** Espera a que la expresión sea verdadera (se evalúa como booleano: un nodo del DOM no vuelve "por valor"). */
  async function esperarHasta(js, ms = 20000) {
    const t = Date.now();
    while (Date.now() - t < ms) { if (await ev(`!!(${js})`)) return true; await dormir(100); }
    return false;
  }
  await enviar("Runtime.enable"); await enviar("Network.enable"); await enviar("Page.enable");
  return { ev, esperarHasta, enviar, errores, cerrar: () => { try { ws.close(); } catch { /* ya cerrado */ } proc.kill(); } };
}

/** Registro de comprobaciones: ok(nombre, condición, detalle) y terminar() -> código de salida (0 si todo pasó). */
export function comprobaciones() {
  const resultados = [];
  const ok = (nombre, cond, detalle = "") => { resultados.push(!!cond); console.log(`${cond ? "✔" : "✘"} ${nombre}${detalle ? " — " + detalle : ""}`); };
  const terminar = () => {
    const mal = resultados.filter((r) => !r).length;
    console.log(`\n${resultados.length - mal}/${resultados.length} comprobaciones correctas`);
    return mal ? 1 : 0;
  };
  return { ok, terminar };
}
