import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, cancelado, COMPONENTES, EVIDENCIA, TEMAS, estadoTxt, hace, textoProcedencia } from "../lib.js";
import { N_MAX, TAMANOS, TEMAS_IDS, VENTANAS, fichaVigente } from "../rutas.js";
import { PESOS_RETO, banda, simular } from "../puntaje.js";
import Ficha from "./Ficha.jsx";
import QuePasariaSi from "./QuePasariaSi.jsx";

/** Una fila de la lista. Memoizada: al cambiar de ficha solo se repinta la que cambia, no las 30. */
const Fila = memo(function Fila({ f, k, activa, corte, onAbrir, sim }) {
  const p = sim ? f.puntaje_sim : f.puntaje;
  const b = sim ? banda(p) : f.banda;
  return (
    <li>
      <button className={"item" + (activa ? " activo" : "")} onClick={() => onAbrir(f.id_caso)} aria-current={activa}>
        <span className="rank">
          {k + 1}
          {sim && f.cambio !== 0 && (
            <small className={"cambio " + (f.cambio > 0 ? "sube" : "baja")} title={`Antes en el puesto ${f.pos_base}`}>
              {f.cambio > 0 ? "▲" : "▼"}{Math.abs(f.cambio)}
            </small>
          )}
        </span>
        <span className="item-cuerpo">
          <span className="kicker">
            {TEMAS[f.tema] || "—"} · {hace(f.fecha_ultima, corte)}
            {f.sintetico && <em className="sint"> · sintético</em>}
          </span>
          <span className="titular">{f.titulo}</span>
          <span className="meta">
            <i className={"punto ev-" + f.estado_evidencia} aria-hidden="true" />
            {EVIDENCIA[f.estado_evidencia]} · {textoProcedencia(f)}
            {f.estado_revision !== "nuevo" && <> · <b>{estadoTxt(f.estado_revision)}</b></>}
          </span>
          <span className="mini" aria-hidden="true">
            {COMPONENTES.map(([c, , w]) => <i key={c} className={"c-" + c} style={{ width: `${f.componentes[c] * w}%` }} />)}
          </span>
        </span>
        <span className={"puntaje banda-" + b} title={sim ? `Simulado: ${p}/100 (oficial ${f.puntaje})` : `Puntaje de atención ${p}/100 (${b})`}>
          {Math.round(p)}
        </span>
      </button>
    </li>
  );
});

/**
 * Agenda. Todo el estado de navegación (tamaño de lista, casos de prueba, ficha, sección) viene de la URL por props;
 * aquí solo se carga datos. Cada carga cancela la anterior (AbortController), así una respuesta lenta del "10" nunca
 * pisa a la del "5": el último clic siempre gana.
 */
export default function Agenda({ corte, ruta, navegar }) {
  const { n, sint, ficha, seccion, tema, dias, c } = ruta;
  const [lista, setLista] = useState({ items: [], total: 0 });
  const [sel, setSel] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [errorLista, setErrorLista] = useState("");
  const [errorFicha, setErrorFicha] = useState("");
  const [version, setVersion] = useState(0);        // sube cuando una revisión/borrador cambia la lista
  const clave = useRef("");
  const [texto, setTexto] = useState("");           // contenido del campo "otro número"
  useEffect(() => { setTexto(typeof n === "number" && !TAMANOS.includes(n) ? String(n) : ""); }, [n]);
  const detalle = useRef(null);
  const [simulando, setSimulando] = useState(false);
  const [pesos, setPesos] = useState({ ...PESOS_RETO });

  // ---- lista ----
  useEffect(() => {
    const ac = new AbortController();
    const nueva = `${n}|${sint}|${tema}|${dias}`;
    if (clave.current !== nueva) { setCargando(true); setLista((l) => ({ ...l, items: [] })); }  // otro filtro: no mostrar la lista vieja
    clave.current = nueva;
    setErrorLista("");
    const filtro = (tema ? `&tema=${tema}` : "") + (dias ? `&dias=${dias}` : "");
    api(`/inbox?limit=${n === "max" ? N_MAX : n}&sinteticos=${sint}${filtro}`, "GET", undefined, ac.signal)
      .then((d) => { setLista({ items: Array.isArray(d?.items) ? d.items : [], total: d?.total ?? 0 }); setCargando(false); })
      .catch((e) => { if (cancelado(e)) return; setErrorLista(e.message); setCargando(false); });
    return () => ac.abort();
  }, [n, sint, tema, dias, version]);

  // ---- ficha: la de la URL; si no hay, la primera de la lista ----
  const idActivo = ficha || lista.items[0]?.id_caso || null;
  useEffect(() => {
    if (!idActivo) { setSel(null); return; }
    const ac = new AbortController();
    setErrorFicha("");
    api("/fichas/" + idActivo, "GET", undefined, ac.signal)
      .then((f) => {
        setSel(f);
        if (ficha && window.innerWidth < 960) detalle.current?.scrollIntoView({ behavior: "smooth" });
      })
      .catch((e) => { if (!cancelado(e)) { setSel(null); setErrorFicha(e.message); } });
    return () => ac.abort();
  }, [idActivo]);

  const abrir = useCallback((id) => navegar({ ficha: id, seccion: "resumen" }), [navegar]);
  // Una respuesta tardía (borrador, revisión) solo cambia la ficha abierta si ES esa ficha; la lista se refresca siempre.
  const actualizar = useCallback((f) => { setSel((actual) => (fichaVigente(f, actual?.id_caso) ? f : actual)); setVersion((v) => v + 1); }, []);
  const vacio = !cargando && !errorLista && lista.items.length === 0;
  // Vista "¿qué pasaría si…?": reordena en el navegador con otros pesos; no toca el backend ni guarda nada.
  const mostrados = useMemo(() => (simulando ? simular(lista.items, pesos) : lista.items), [simulando, lista.items, pesos]);
  const que = sint ? "casos de prueba" : "temas";
  const faltan = !cargando && !errorLista && typeof n === "number" && lista.total > 0 && lista.total < n;  // pidió más de los que existen

  const aplicarTexto = () => {
    const v = Math.floor(Number(texto));
    if (!texto.trim() || !Number.isFinite(v)) return;
    navegar({ n: Math.min(Math.max(v, 1), N_MAX), ficha, seccion });
  };

  return (
    <div className="agenda">
      <section className="lista" aria-label="Agenda priorizada">
        <div className="lista-cab">
          <div>
            <p className="kicker">{sint ? "Casos de prueba controlados" : "Agenda de Panamá"}</p>
            <h1>{sint ? "Casos sintéticos" : n === "max" ? `Todos los temas (${lista.total})` : `Top ${n} para revisar`}</h1>
          </div>
        </div>
        <div className="selector-n" role="group" aria-label={`Cuántos ${que} ver`}>
          <div className="segmentos">
            {TAMANOS.map((t) => (
              <button key={t} className={n === t ? "seg on" : "seg"} aria-pressed={n === t}
                onClick={() => navegar({ n: t, ficha, seccion })}>{t}</button>
            ))}
          </div>
          <form className="otro-n" onSubmit={(e) => { e.preventDefault(); aplicarTexto(); }}>
            <label htmlFor="otro-n">Otro número</label>
            <input id="otro-n" type="number" inputMode="numeric" min={1} max={N_MAX} placeholder="ej. 12" value={texto}
              onChange={(e) => setTexto(e.target.value)} />
            <button type="submit" className="seg ver" disabled={!texto.trim()}>Ver</button>
          </form>
          <button className={n === "max" ? "seg on max" : "seg max"} aria-pressed={n === "max"}
            title={`Mostrar todos los ${que} disponibles`} onClick={() => navegar({ n: "max", ficha, seccion })}>Máx</button>
          <button className={simulando ? "seg on max" : "seg max"} aria-pressed={simulando} onClick={() => setSimulando((s) => !s)}
            title="Cambiar los pesos del puntaje y ver cómo cambiaría el orden, sin guardar nada">¿Qué pasaría si…?</button>
        </div>
        {simulando && <QuePasariaSi pesos={pesos} setPesos={setPesos} cuantos={lista.items.length} />}
        <div className="filtros-tema" role="group" aria-label="Filtrar la agenda">
          <label>Tema
            <select value={tema || ""} onChange={(e) => navegar({ tema: e.target.value || null, ficha: null, c: "" })}>
              <option value="">Todos</option>
              {TEMAS_IDS.map((t) => <option key={t} value={t}>{TEMAS[t]}</option>)}
            </select>
          </label>
          <label>Periodo
            <select value={dias || ""} onChange={(e) => navegar({ dias: e.target.value ? Number(e.target.value) : null, ficha: null, c: "" })}>
              <option value="">Todo el snapshot</option>
              {VENTANAS.map((d) => <option key={d} value={d}>{d === 1 ? "Último día" : `Últimos ${d} días`}</option>)}
            </select>
          </label>
        </div>
        {(tema || dias) && (
          <p className="filtro-activo" role="status">
            {c ? <>Filtrado por tu consulta «{c}»: </> : <>Filtro: </>}
            <b>{tema ? TEMAS[tema] : "todos los temas"}{dias ? ` · últimos ${dias} día${dias === 1 ? "" : "s"} (respecto del corte)` : ""}</b>
            <button className="quitar-filtro" onClick={() => navegar({ tema: null, dias: null, c: "", ficha: null })}>Quitar filtro ✕</button>
          </p>
        )}
        <label className="interruptor">
          <input type="checkbox" checked={sint} onChange={(e) => navegar({ sint: e.target.checked, ficha: null })} />
          <span>Ver casos de prueba (inyección, contradicciones, recirculada, agencia replicada)</span>
        </label>

        {errorLista && (
          <div className="error-caja" role="alert">
            <p>{errorLista}</p>
            <button onClick={() => setVersion((v) => v + 1)}>Reintentar</button>
          </div>
        )}
        {cargando && !errorLista && <p className="vacio" aria-live="polite">Cargando agenda…</p>}
        {faltan && (
          <p className="aviso-n" role="status">
            Solo hay {lista.total} {que} disponibles, así que no se pueden mostrar {n}. Son todos los que existen.
          </p>
        )}
        {vacio && <p className="vacio">No hay temas para mostrar con este filtro. Prueba con otro tema, un periodo más largo o quita el filtro.</p>}

        <ol className="items" aria-busy={cargando}>
          {mostrados.map((f, k) => <Fila key={f.id_caso} f={f} k={k} activa={idActivo === f.id_caso} corte={corte} onAbrir={abrir} sim={simulando} />)}
        </ol>
        {lista.items.length > 0 && (
          <p className="nota">
            Mostrando {lista.items.length} de {lista.total} {que}. El puntaje ordena la atención (P = 30R + 25I + 20U + 15N + 10E); no es
            probabilidad de verdad. La evidencia se evalúa aparte.
          </p>
        )}
      </section>

      <section className="detalle" aria-label="Ficha del tema" ref={detalle}>
        {errorFicha && (
          <div className="error-caja" role="alert">
            <p>{errorFicha}</p>
            <button onClick={() => navegar({ ficha: null })}>Volver a la lista</button>
          </div>
        )}
        {sel && sel.id_caso === idActivo && (
          <Ficha f={sel} corte={corte} seccion={seccion} onSeccion={(s) => navegar({ ficha: sel.id_caso, seccion: s })} onCambio={actualizar} />
        )}
        {!sel && !errorFicha && <p className="vacio">{cargando ? "Cargando…" : "Selecciona un tema."}</p>}
      </section>
    </div>
  );
}
