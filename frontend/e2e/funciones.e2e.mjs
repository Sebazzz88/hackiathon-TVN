// Prueba de extremo a extremo de las funciones nuevas, en un navegador REAL sin ventana (ver navegador.mjs).
// Requiere la app encendida (APP_URL, por defecto http://localhost:5173) y Node 22+.
//   node e2e/funciones.e2e.mjs
// Cubre: "Otro número" y "Máx" (reales y sintéticos), generar y REGENERAR borrador, fuente normal en las citas,
// visor de evidencia, banner de titular/metadatos, Modo jurado en vivo y accesibilidad básica.
import { URL_APP, abrirNavegador, comprobaciones, dormir } from "./navegador.mjs";

const { ok, terminar } = comprobaciones();
let nav;
try {
  nav = await abrirNavegador(9334);
  const { ev, esperarHasta, enviar, errores } = nav;
  const ir = async (hash) => { await ev(`location.hash = ${JSON.stringify(hash)}`); await dormir(150); };
  const asentado = (n) => esperarHasta(`document.querySelectorAll('.items li').length === ${n} && document.querySelector('.items')?.getAttribute('aria-busy') === 'false'`);
  const clicTexto = (sel, re) => ev(`[...document.querySelectorAll(${JSON.stringify(sel)})].find(b => ${re}.test(b.textContent.trim()))?.click()`);
  const api = (p) => ev(`fetch(${JSON.stringify(p)}).then(r => r.json())`);

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
  await ir("#/agenda?n=30&p=1");
  await asentado(sint);
  ok("y dice cuántos hay cuando se piden más de los que existen", await ev("document.body.textContent.includes('" + sint + "')"));

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
  await ev("window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))");
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

  ok("sin errores de servidor (5xx) en toda la sesión", errores.red.length === 0, errores.red.join(" | "));
  ok("sin excepciones en la consola del navegador", errores.consola.length === 0, errores.consola.join(" | "));
} catch (e) {
  console.error("Fallo del script:", e); ok("el script terminó sin excepciones", false);
} finally {
  nav?.cerrar();
  process.exit(terminar());
}
