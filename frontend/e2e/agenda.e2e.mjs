// Prueba de extremo a extremo de la agenda en un navegador REAL sin ventana (ver navegador.mjs).
// Requiere la app encendida (APP_URL, por defecto http://localhost:5173) y Node 22+.
//   node e2e/agenda.e2e.mjs
// Reproduce los fallos reportados: cambiar 5 -> 10 -> 5, elegir 30, casos de prueba con 5/10, clics rápidos.
import { URL_APP, abrirNavegador, comprobaciones, dormir } from "./navegador.mjs";

const { ok, terminar } = comprobaciones();
let nav;
try {
  nav = await abrirNavegador(9333);
  const { ev, esperarHasta, enviar, errores } = nav;
  const filas = () => ev("document.querySelectorAll('.items li').length");
  const h1 = () => ev("document.querySelector('.lista h1')?.textContent");
  const hayError = () => ev("!!document.querySelector('.error-caja, .aviso-global')");
  const clic = (sel, texto) => ev(`[...document.querySelectorAll(${JSON.stringify(sel)})].find(b => b.textContent.trim() === ${JSON.stringify(texto)})?.click()`);
  const asentado = (n) => esperarHasta(`document.querySelectorAll('.items li').length === ${n} && document.querySelector('.items')?.getAttribute('aria-busy') === 'false'`);

  await enviar("Page.navigate", { url: URL_APP + "/#/agenda" });
  ok("la agenda carga con 5 temas", await asentado(5), `h1="${await h1()}"`);

  // --- Reporte 1: abrir 10 y volver a 5 se quedaba en 10
  await clic(".seg", "10"); ok("al elegir 10 hay 10 temas", await asentado(10));
  await clic(".seg", "5");  ok("al volver a 5 hay 5 temas (antes se quedaba en 10)", await asentado(5), `h1="${await h1()}"`);
  ok("el título dice Top 5", (await h1()) === "Top 5 para revisar");

  // --- Clics rápidos, sin esperar: el último debe ganar aunque las respuestas lleguen desordenadas
  for (const t of ["10", "30", "5", "10", "5", "30", "10", "5"]) await clic(".seg", t);
  ok("tras clics rápidos 10,30,5,10,5,30,10,5 queda exactamente en 5", await asentado(5),
    `h1="${await h1()}" hash=${await ev("location.hash")} pantalla="${(await ev("document.querySelector('.contenido')?.innerText || ''")).slice(0, 200).replace(/\s+/g, " ")}"`);
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
  ok("abrir una ficha sintética no apaga los casos de prueba", await esperarHasta("document.querySelector('.ficha-cab .sint')") && await ev("document.querySelector('.interruptor input').checked"),
    await ev("location.hash + ' | ' + (document.querySelector('.ficha-cab .kicker')?.textContent || 'sin ficha') + ' | marcada=' + document.querySelector('.interruptor input')?.checked + ' | filas=' + document.querySelectorAll('.items .item').length"));
  await ev("history.back()"); await dormir(500);
  ok("sin errores de servidor (5xx) en toda la sesión", errores.red.length === 0, errores.red.join(" | "));
  ok("sin excepciones en la consola del navegador", errores.consola.length === 0, errores.consola.join(" | "));
} catch (e) {
  console.error("Fallo del script:", e); ok("el script terminó sin excepciones", false);
} finally {
  nav?.cerrar();
  process.exit(terminar());
}
