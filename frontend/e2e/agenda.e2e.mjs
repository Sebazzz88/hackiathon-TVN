// Prueba de extremo a extremo en un navegador REAL (Edge o Chrome), sin dependencias: habla con él por el protocolo
// de depuración (CDP). Requiere la app encendida en http://localhost:5173 y Node 22+.
//   node e2e/agenda.e2e.mjs
// Reproduce los fallos reportados: cambiar 5 -> 10 -> 5, elegir 30, casos de prueba con 5/10, clics rápidos.
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const URL_APP = process.env.APP_URL || "http://localhost:5173";
const PUERTO = 9333;
const NAVEGADORES = [
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
];
const exe = NAVEGADORES.find(existsSync);
if (!exe) { console.error("No encontré Edge ni Chrome."); process.exit(2); }

const proc = spawn(exe, ["--headless=new", `--remote-debugging-port=${PUERTO}`, "--disable-gpu", "--window-size=1440,1000",
  `--user-data-dir=${mkdtempSync(join(tmpdir(), "tvn-e2e-"))}`, "about:blank"], { stdio: "ignore" });
const dormir = (ms) => new Promise((r) => setTimeout(r, ms));

let ws, idMsg = 0, pendientes = new Map(), erroresConsola = [], erroresRed = [];
async function conectar() {
  for (let i = 0; i < 40; i++) {
    try {
      const paginas = await (await fetch(`http://localhost:${PUERTO}/json`)).json();
      const p = paginas.find((x) => x.type === "page");
      if (p) { ws = new WebSocket(p.webSocketDebuggerUrl); await new Promise((ok, no) => { ws.onopen = ok; ws.onerror = no; }); return; }
    } catch { /* aún arrancando */ }
    await dormir(250);
  }
  throw new Error("No pude conectar con el navegador");
}
const enviar = (method, params = {}) => new Promise((ok) => { const id = ++idMsg; pendientes.set(id, ok); ws.send(JSON.stringify({ id, method, params })); });
const ev = async (js) => (await enviar("Runtime.evaluate", { expression: js, returnByValue: true, awaitPromise: true })).result?.result?.value;
async function esperarHasta(js, ms = 20000) { const t = Date.now(); while (Date.now() - t < ms) { if (await ev(js)) return true; await dormir(100); } return false; }

const resultados = [];
const ok = (nombre, cond, detalle = "") => { resultados.push({ nombre, cond: !!cond }); console.log(`${cond ? "✔" : "✘"} ${nombre}${detalle ? " — " + detalle : ""}`); };
const filas = () => ev("document.querySelectorAll('.items li').length");
const h1 = () => ev("document.querySelector('.lista h1')?.textContent");
const hayError = () => ev("!!document.querySelector('.error-caja, .aviso-global')");
const clic = (sel, texto) => ev(`[...document.querySelectorAll(${JSON.stringify(sel)})].find(b => b.textContent.trim() === ${JSON.stringify(texto)})?.click()`);
const asentado = (n) => esperarHasta(`document.querySelectorAll('.items li').length === ${n} && document.querySelector('.items')?.getAttribute('aria-busy') === 'false'`);

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

  ok("la agenda carga con 5 temas", await asentado(5), `h1="${await h1()}"`);

  // --- Reporte 1: abrir 10 y volver a 5 se quedaba en 10
  await clic(".seg", "10"); ok("al elegir 10 hay 10 temas", await asentado(10));
  await clic(".seg", "5");  ok("al volver a 5 hay 5 temas (antes se quedaba en 10)", await asentado(5), `h1="${await h1()}"`);
  ok("el título dice Top 5", (await h1()) === "Top 5 para revisar");

  // --- Clics rápidos, sin esperar: el último debe ganar aunque las respuestas lleguen desordenadas
  for (const t of ["10", "30", "5", "10", "5", "30", "10", "5"]) await clic(".seg", t);
  ok("tras clics rápidos 10,30,5,10,5,30,10,5 queda exactamente en 5", await asentado(5), `h1="${await h1()}"`);
  await dormir(1500);
  ok("y sigue en 5 después de que lleguen respuestas tardías", (await filas()) === 5);

  // --- Reporte 2: elegir 30 daba error 500
  await clic(".seg", "30"); ok("al elegir 30 hay 30 temas, sin error", await asentado(30) && !(await hayError()));

  // --- Reporte 3: casos de prueba + 5/10 se "bugueaban"
  await clic(".seg", "5");
  await ev("document.querySelector('.interruptor input').click()");
  ok("casos de prueba activados", await esperarHasta("document.querySelector('.lista h1')?.textContent === 'Casos sintéticos'"));
  await clic(".seg", "10");
  ok("casos de prueba + 10: sin error y solo sintéticos", await esperarHasta("document.querySelectorAll('.items li').length > 0") && !(await hayError())
    && await ev("[...document.querySelectorAll('.items li')].every(li => li.textContent.includes('sintético'))"), `${await filas()} filas`);
  await clic(".seg", "5");
  ok("casos de prueba + 5: sin error y 5 filas", await asentado(5) && !(await hayError()));
  ok("la casilla sigue marcada (nada la reactivó ni la apagó)", await ev("document.querySelector('.interruptor input').checked"));
  await ev("document.querySelector('.interruptor input').click()");
  ok("al desmarcar vuelve a la agenda real", await esperarHasta("document.querySelector('.lista h1')?.textContent === 'Top 5 para revisar'") && await asentado(5));
  ok("la ficha abierta es del tema real (no sintética)", await esperarHasta("document.querySelector('.ficha-cab h2') && !document.querySelector('.ficha-cab .sint')"));

  // --- Ficha sintética abierta desde el listado y botón atrás
  await ev("document.querySelector('.interruptor input').click()");
  await esperarHasta("document.querySelector('.lista h1')?.textContent === 'Casos sintéticos' && document.querySelectorAll('.items .item').length > 1");
  await ev("document.querySelectorAll('.items .item')[1].click()");
  ok("abrir una ficha sintética no apaga los casos de prueba", await esperarHasta("!!document.querySelector('.ficha-cab .sint')") && await ev("document.querySelector('.interruptor input').checked"),
    await ev("location.hash + ' | ' + (document.querySelector('.ficha-cab .kicker')?.textContent || 'sin ficha') + ' | marcada=' + document.querySelector('.interruptor input')?.checked + ' | filas=' + document.querySelectorAll('.items .item').length"));
  await ev("history.back()"); await dormir(500);
  ok("sin errores de servidor (5xx) en toda la sesión", erroresRed.length === 0, erroresRed.join(" | "));
  ok("sin excepciones en la consola del navegador", erroresConsola.length === 0, erroresConsola.join(" | "));
} catch (e) {
  console.error("Fallo del script:", e); ok("el script terminó sin excepciones", false);
} finally {
  try { ws?.close(); } catch {}
  proc.kill();
  const mal = resultados.filter((r) => !r.cond).length;
  console.log(`\n${resultados.length - mal}/${resultados.length} comprobaciones correctas`);
  process.exit(mal ? 1 : 0);
}
