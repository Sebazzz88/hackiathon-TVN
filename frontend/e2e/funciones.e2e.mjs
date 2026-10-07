// Prueba de extremo a extremo de las funciones nuevas, en un navegador REAL sin ventana (Edge/Chrome headless, CDP).
// Requiere la app encendida (APP_URL, por defecto http://localhost:5173) y Node 22+.
//   node e2e/funciones.e2e.mjs
// Cubre: "Otro número" y "Máx" (reales y sintéticos), generar y REGENERAR borrador, fuente normal en las citas,
// visor de evidencia, banner de titular/metadatos, Modo jurado en vivo y accesibilidad básica.
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const URL_APP = process.env.APP_URL || "http://localhost:5173";
const PUERTO = 9334;
const exe = ["C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
  "C:/Program Files/Google/Chrome/Application/chrome.exe"].find(existsSync);
if (!exe) { console.error("No encontré Edge ni Chrome."); process.exit(2); }
const proc = spawn(exe, ["--headless=new", `--remote-debugging-port=${PUERTO}`, "--disable-gpu", "--window-size=1440,1000",
  `--user-data-dir=${mkdtempSync(join(tmpdir(), "tvn-e2e-"))}`, "about:blank"], { stdio: "ignore" });
const dormir = (ms) => new Promise((r) => setTimeout(r, ms));

let ws, idMsg = 0;
const pendientes = new Map(), erroresConsola = [], erroresRed = [];
async function conectar() {
  for (let i = 0; i < 40; i++) {
    try {
      const p = (await (await fetch(`http://localhost:${PUERTO}/json`)).json()).find((x) => x.type === "page");
      if (p) { ws = new WebSocket(p.webSocketDebuggerUrl); await new Promise((ok, no) => { ws.onopen = ok; ws.onerror = no; }); return; }
    } catch { /* aún arrancando */ }
    await dormir(250);
  }
  throw new Error("No pude conectar con el navegador");
}
const enviar = (method, params = {}) => new Promise((ok) => { const id = ++idMsg; pendientes.set(id, ok); ws.send(JSON.stringify({ id, method, params })); });
const ev = async (js) => (await enviar("Runtime.evaluate", { expression: js, returnByValue: true, awaitPromise: true })).result?.result?.value;
async function esperarHasta(js, ms = 20000) { const t = Date.now(); while (Date.now() - t < ms) { if (await ev(`!!(${js})`)) return true; await dormir(100); } return false; }
const ir = async (hash) => { await ev(`location.hash = ${JSON.stringify(hash)}`); await dormir(150); };
const asentado = (n) => esperarHasta(`document.querySelectorAll('.items li').length === ${n} && document.querySelector('.items')?.getAttribute('aria-busy') === 'false'`);
const clicTexto = (sel, re) => ev(`[...document.querySelectorAll(${JSON.stringify(sel)})].find(b => ${re}.test(b.textContent.trim()))?.click()`);
const api = (p) => ev(`fetch(${JSON.stringify(p)}).then(r => r.json())`);

const resultados = [];
const ok = (nombre, cond, detalle = "") => { resultados.push(!!cond); console.log(`${cond ? "✔" : "✘"} ${nombre}${detalle ? " — " + detalle : ""}`); };

try {
  await conectar();
  ws.onmessage = (m) => {
    const d = JSON.parse(m.data);
    if (d.id && pendientes.has(d.id)) { pendientes.get(d.id)(d); pendientes.delete(d.id); }
    else if (d.method === "Runtime.exceptionThrown") erroresConsola.push(d.params.exceptionDetails.text + " " + (d.params.exceptionDetails.exception?.description || ""));
    else if (d.method === "Network.responseReceived" && d.params.response.status >= 500) erroresRed.push(`${d.params.response.status} ${d.params.response.url}`);
  };
  await enviar("Runtime.enable"); await enviar("Network.enable"); await enviar("Page.enable");
  await enviar("Page.navigate", { url: URL_APP + "/#/agenda" });
  await asentado(5);

  // --- Otro número y Máx
  await ev(`(() => { const i = document.getElementById('otro-n');
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(i, '12');
    i.dispatchEvent(new Event('input', { bubbles: true })); })()`);
  await dormir(100);
  await clicTexto(".otro-n button", "/^Ver$/");
  ok("«Otro número» = 12 muestra 12 temas", await asentado(12), await ev("location.hash"));
  const reales = (await api("/api/inbox?limit=1000")).total;
  await clicTexto(".seg", "/^Máx$/");
  ok(`«Máx» muestra todos los temas reales (${reales})`, await asentado(reales), await ev("document.querySelector('.lista h1')?.textContent"));
  const sint = (await api("/api/inbox?limit=1000&sinteticos=true")).total;
  await ev("document.querySelector('.interruptor input').click()");
  ok(`casos de prueba + Máx muestra los ${sint} existentes`, await asentado(sint));
  ok("y dice cuántos hay cuando se piden más de los que existen",
    await (async () => { await ir("#/agenda?n=30&p=1"); await asentado(sint); return ev("document.body.textContent.includes('" + sint + "')"); })());

  // --- Ficha: banner, citas con fuente normal y visor de evidencia
  await ir("#/ficha/EV-G226d8217c0/resumen");
  ok("la ficha abre", await esperarHasta("document.querySelector('.ficha-cab h2')"));
  ok("banner «basado únicamente en titular/metadatos» visible en la ficha",
    await esperarHasta("[...document.querySelectorAll('.ficha .banner-metadatos')].some(e => e.offsetParent && /titular\\/metadatos/.test(e.textContent))"));
  ok("las citas usan la misma letra que el texto (no monoespaciada)",
    await esperarHasta("document.querySelector('.cita')") &&
    await ev("getComputedStyle(document.querySelector('.cita')).fontFamily === getComputedStyle(document.body).fontFamily"),
    await ev("getComputedStyle(document.querySelector('.cita'))?.fontFamily"));
  await ev("document.querySelector('.cita').click()");
  ok("una cita abre el registro fuente", await esperarHasta("document.querySelector('.visor[role=dialog]')"));
  await ev("document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' })); window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))");
  ok("Escape cierra el visor", await esperarHasta("!document.querySelector('.visor')", 3000));

  // --- Borrador: generar y regenerar
  await ir("#/ficha/EV-G226d8217c0/borrador");
  ok("banner de titular/metadatos también en el borrador", await esperarHasta("document.querySelector('.panel .banner-metadatos')"));
  await esperarHasta("[...document.querySelectorAll('.barra-accion button.primario')].some(b => !b.disabled)");
  await clicTexto(".barra-accion button.primario", "/Generar|Regenerar/");
  ok("generar borrador muestra el paquete", await esperarHasta("document.querySelector('.paquete')", 120000));
  const antes = await ev("document.querySelector('.generador')?.textContent || ''");
  await clicTexto(".barra-accion button.primario", "/^Regenerar borrador$/");
  ok("«Regenerar borrador» arranca", await esperarHasta("/Generando|Regenerar/.test(document.querySelector('.barra-accion button.primario')?.textContent)", 3000));
  ok("y vuelve a mostrar el paquete, sin error",
    await esperarHasta("document.querySelector('.paquete') && !document.querySelector('.barra-accion button.primario').disabled", 120000)
    && !(await ev("!!document.querySelector('.panel .error-caja')")), antes.trim());

  // --- Modo jurado
  await ir("#/jurado");
  ok("pestaña Modo jurado", await esperarHasta("/T01–T10/.test(document.querySelector('.jurado h1')?.textContent)"));
  await clicTexto(".jurado button.primario", "/Correr/");
  ok("correr T01–T10 en vivo: 10 en verde", await esperarHasta("document.querySelectorAll('.prueba-j.verde').length === 10", 180000),
    await ev("document.querySelector('.barra-accion .nota')?.textContent"));
  ok("métricas con numerador/denominador leídas de eval/results.json",
    await esperarHasta("[...document.querySelectorAll('.tabla.metricas td.num b')].length > 0"));

  // --- Accesibilidad
  ok("enlace «Saltar al contenido» que lleva al foco al contenido",
    await ev("(() => { const a = document.querySelector('a.saltar'); a.click(); return document.activeElement?.id === 'contenido'; })()"));
  ok("foco visible definido", await ev("[...document.styleSheets].some(s => { try { return [...s.cssRules].some(r => r.selectorText === ':focus-visible'); } catch { return false; } })"));

  ok("sin errores de servidor (5xx) en toda la sesión", erroresRed.length === 0, erroresRed.join(" | "));
  ok("sin excepciones en la consola del navegador", erroresConsola.length === 0, erroresConsola.join(" | "));
} catch (e) {
  console.error("Fallo del script:", e); ok("el script terminó sin excepciones", false);
} finally {
  try { ws?.close(); } catch {}
  proc.kill();
  const mal = resultados.filter((r) => !r).length;
  console.log(`\n${resultados.length - mal}/${resultados.length} comprobaciones correctas`);
  process.exit(mal ? 1 : 0);
}
