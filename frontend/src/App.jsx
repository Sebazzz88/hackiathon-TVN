import { useEffect, useState } from "react";

async function api(path, method = "GET", body) {
  const r = await fetch(path.startsWith("/health") ? path : "/api" + path, {
    method, headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined,
  });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(typeof d.detail === "string" ? d.detail : "Error " + r.status);
  return d;
}

const ESTADOS = ["nuevo", "en_revision", "requiere_evidencia", "aprobado_como_borrador", "descartado"];
const TEMAS = { economia: "Economía", logistica_canal: "Logística / Canal", turismo: "Turismo", servicios_publicos: "Servicios públicos",
  eventos_naturales: "Eventos naturales", regulacion: "Regulación", otros: "Fuera de los 6 temas" };
const COMP = { R: ["Relevancia", 30], I: ["Impacto potencial", 25], U: ["Urgencia", 20], N: ["Novedad", 15], E: ["Evidencia disponible", 10] };
const txt = (s) => (s || "").replaceAll("_", " ");
const fmtPA = new Intl.DateTimeFormat("es-PA", { timeZone: "America/Panama", day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
const horaPA = (s) => (s ? fmtPA.format(new Date(s)) + " (hora de Panamá)" : "sin dato");

function Citas({ citas }) {
  return <span className="chips">{citas.map((c, i) => <code key={i} title={c.campo}>{c.id_evidencia}·{c.campo}</code>)}</span>;
}

function Calidad({ q }) {
  if (!q || q.disponible === false) return <p className="vacio">Reporte de calidad no disponible: corre <code>validate.py</code>.</p>;
  const n = q.noticias || {};
  return (
    <div className="calidad">
      <div className="kpis">
        <div><b>{n.validas ?? q.validas}</b><span>noticias válidas</span></div>
        <div><b>{n.con_error ?? q.con_error}</b><span>con error (separadas)</span></div>
        <div><b>{n.tvn_validas ?? "—"}</b><span>de TVN</span></div>
        <div><b>{q.indicadores ? `${q.indicadores.con_valor}/${q.indicadores.celdas}` : "—"}</b><span>celdas BM con valor</span></div>
        <div><b>{q.eventos?.total ?? "—"}</b><span>sismos USGS 2024</span></div>
      </div>
      <details><summary>Detalle del reporte</summary>
        <p>Cobertura: {horaPA(n.cobertura?.desde)} → {horaPA(n.cobertura?.hasta)} · {n.medios_distintos} medios · {n.sin_fecha_publicacion} sin fecha de publicación (GDELT solo da detección).</p>
        <p>Errores: {Object.entries(n.errores_por_tipo || {}).map(([k, v]) => `${k}: ${v}`).join(" · ") || "ninguno"}</p>
        {q.indicadores && <p>Banco Mundial: {q.indicadores.nulas} celdas nulas conservadas (no se rellenan con 0) de {q.indicadores.esperadas} esperadas.</p>}
        {q.eventos && <p>USGS: {q.eventos.nota}</p>}
      </details>
    </div>
  );
}

function Barras({ f }) {
  return (
    <table className="comp">
      <tbody>
        {Object.entries(COMP).map(([k, [nom, peso]]) => (
          <tr key={k}>
            <th>{k} · {nom} <small>×{peso}</small></th>
            <td><div className="barra"><i style={{ width: `${f.componentes[k] * 100}%` }} /></div></td>
            <td className="num">{(f.componentes[k] * peso).toFixed(1)}</td>
            <td className="just">{f.justificacion?.[k]}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function Borrador({ b }) {
  if (b.stub) return <p className="vacio">{b.brief}</p>;
  if (b.abstencion) return <p className="faltante">{b.faltante?.join(" ")}</p>;
  const sec = (s) => b.afirmaciones.filter((a) => a.seccion === s);
  const Lista = ({ s }) => <ul className="afirm">{sec(s).map((a, i) => <li key={i}><span className={"tipo t-" + a.tipo}>{a.tipo}</span> {a.texto} <Citas citas={a.citas} /></li>)}</ul>;
  return (
    <div className="borrador">
      <p className="aviso">{b.aviso} · Generador: <code>{b.generador}</code>{b.meta_llm?.costo_usd != null && ` · costo ${b.meta_llm.costo_usd} USD`}</p>
      <h4>Título propuesto</h4><p><b>{b.titulo}</b></p>
      {b.enfoque && <><h4>Enfoque de interés público</h4><p><span className={"tipo t-" + b.enfoque.tipo}>{b.enfoque.tipo}</span> {b.enfoque.texto} <Citas citas={b.enfoque.citas} /></p></>}
      <h4>Brief ({b.brief_palabras}/250 palabras)</h4><p className="leyenda">{b.leyenda}</p><Lista s="brief" />
      <h4>3 preguntas de investigación</h4><ol>{b.preguntas.map((p) => <li key={p}>{p}</li>)}</ol>
      <h4>Fuentes y verificaciones pendientes</h4><ul>{b.verificaciones_pendientes.map((p) => <li key={p} className="faltante">{p}</li>)}</ul>
      <h4>Guion (~{b.guion_segundos_estimados} s)</h4>{b.guion_aviso && <p className="faltante">{b.guion_aviso}</p>}<Lista s="guion" />
      <h4>Copy digital ({b.copy_palabras}/80 palabras)</h4><Lista s="copy" />
      <p className="nota">Cobertura de citas: {b.cobertura_citas.con_cita_valida}/{b.cobertura_citas.emitidas} afirmaciones emitidas con cita válida.</p>
      {b.eliminadas?.length > 0 && <details><summary>{b.eliminadas.length} afirmación(es) eliminadas por el validador</summary>
        <ul>{b.eliminadas.map((e, i) => <li key={i}>[{e.seccion}] {e.texto} — <i>{e.motivo}</i></li>)}</ul></details>}
    </div>
  );
}

function Evaluacion({ ev }) {
  if (!ev) return null;
  const e = ev.evaluacion || {};
  return (
    <section>
      <h2>Panel de evaluación</h2>
      {ev.agente?.agente && <p className="nota">Agente {ev.agente.agente} · embeddings: <b>{ev.agente.embeddings}</b> · {ev.agente.noticias} titulares → {ev.agente.eventos} eventos en {ev.agente.segundos_pipeline} s.</p>}
      {e.disponible === false ? <p className="vacio">Aún no hay resultados: corre <code>python eval/run_eval.py</code>.</p> : (
        <>
          <p className="nota">Ejecución: {horaPA(e.generado_utc)} · conjunto: {e.conjunto}. Etiquetas: {e.etiquetas}</p>
          <table className="metricas"><thead><tr><th>Métrica</th><th>Agente (IA)</th><th>Baseline</th><th>Nota</th></tr></thead>
            <tbody>{(e.metricas || []).map((m) => (
              <tr key={m.nombre}><td>{m.nombre}</td><td>{m.agente}</td><td>{m.baseline ?? "—"}</td><td className="just">{m.nota}</td></tr>
            ))}</tbody></table>
        </>
      )}
    </section>
  );
}

export default function App() {
  const [items, setItems] = useState([]);
  const [sint, setSint] = useState(false);
  const [lim, setLim] = useState(5);
  const [sel, setSel] = useState(null);
  const [q, setQ] = useState("");
  const [ans, setAns] = useState(null);
  const [revisor, setRevisor] = useState("");
  const [coment, setComent] = useState("");
  const [msg, setMsg] = useState("");
  const [cal, setCal] = useState(null);
  const [ev, setEv] = useState(null);
  const [health, setHealth] = useState(null);
  const [busy, setBusy] = useState(false);
  const fail = (e) => { setMsg(e.message); setBusy(false); };
  const load = () => api(`/inbox?limit=${lim}&sinteticos=${sint}`).then(setItems).catch(fail);
  useEffect(() => { load(); }, [sint, lim]);
  useEffect(() => {
    api("/quality-report").then(setCal).catch(() => {});
    api("/eval").then(setEv).catch(() => {});
    api("/health").then(setHealth).catch(() => {});
  }, []);

  const open = (id) => { setMsg(""); api("/fichas/" + id).then(setSel).catch(fail); };
  const draft = () => { setBusy(true); api(`/fichas/${sel.id_caso}/draft`, "POST").then((f) => { setSel(f); setBusy(false); load(); }).catch(fail); };
  const review = (estado) => {
    if (revisor.trim().length < 2) return setMsg("Escribe el nombre de la persona revisora.");
    api(`/fichas/${sel.id_caso}/review`, "POST", { estado, revisor, comentario: coment })
      .then((f) => { setSel(f); setMsg(""); setComent(""); load(); }).catch(fail);
  };
  const ask = () => { if (q.trim().length < 3) return; setMsg(""); api("/query", "POST", { pregunta: q }).then(setAns).catch(fail); };

  return (
    <main>
      <header>
        <h1>Copiloto TVN · De la señal a la decisión</h1>
        <p className="nota">Modo {health?.agent_mode ?? "…"} · reglas {health?.reglas} · P = 30R + 25I + 20U + 15N + 10E · Las salidas son borradores: nada se publica automáticamente.</p>
      </header>
      {msg && <p className="alerta" role="alert">{msg}</p>}

      <section className="paso"><h2><span className="n">1</span> Reporte de calidad del snapshot</h2><Calidad q={cal} /></section>

      <div className="cols">
        <section>
          <h2><span className="n">2</span> Bandeja priorizada</h2>
          <div className="filtros">
            <label><input type="checkbox" checked={sint} onChange={(e) => { setSint(e.target.checked); setSel(null); }} /> Casos controlados sintéticos (T02, T03, T05, T07)</label>
            <select value={lim} onChange={(e) => setLim(+e.target.value)} aria-label="Cantidad"><option value={5}>Top 5</option><option value={10}>Top 10</option><option value={30}>Top 30</option></select>
          </div>
          {items.map((f, k) => (
            <button key={f.id_caso} className={"fila" + (sel?.id_caso === f.id_caso ? " activa" : "")} onClick={() => open(f.id_caso)}>
              <span className="pts">{f.puntaje}<small>{f.banda}</small></span>
              <span className="tit">{k + 1}. {f.titulo}{f.sintetico && <em> (caso sintético)</em>}
                <small>{TEMAS[f.tema] || f.tema} · {f.registros || f.ids_fuente.length} titular(es) · {f.fuentes_independientes} procedencia(s) · {txt(f.estado_revision)}</small>
                <span className="mini">{Object.keys(COMP).map((c) => <i key={c} title={c} style={{ width: `${f.componentes[c] * COMP[c][1]}%` }} className={"c-" + c} />)}</span>
              </span>
              <span className={"tag ev-" + f.estado_evidencia}>evidencia {txt(f.estado_evidencia)}</span>
            </button>
          ))}
          <p className="nota">Puntaje = orden de atención, no probabilidad de verdad. Estado de evidencia es independiente del puntaje. Empates: mayor U, luego ID.</p>

          <h2><span className="n">·</span> Consulta en español</h2>
          <div className="consulta">
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ej.: ¿Cuál fue la inflación de Panamá en 2023?" onKeyDown={(e) => e.key === "Enter" && ask()} />
            <button onClick={ask}>Consultar</button>
          </div>
          {ans && (
            <div className="resp">
              {ans.abstencion ? <b>Abstención: no hay evidencia suficiente para responder.</b> : <p className="pre">{ans.respuesta}</p>}
              {ans.faltante.map((f) => <p key={f} className="faltante">Falta: {f}</p>)}
              {ans.versiones?.length > 0 && <p className="faltante">Versiones incompatibles visibles: el sistema no elige una.</p>}
              {ans.citas.map((c, i) => <p key={i} className="cita">[{c.tipo}] {c.afirmacion} — <code>{c.id_evidencia}·{c.campo}</code></p>)}
              <p className="nota">Método: {ans.metodo} · base: {ans.base}</p>
            </div>
          )}
        </section>

        <section>
          {!sel ? <p className="vacio">Abre un tema de la bandeja para ver su ficha.</p> : (
            <article>
              <h2><span className="n">3</span> Ficha · {sel.titulo}</h2>
              <p>Puntaje <b>{sel.puntaje}/100 ({sel.banda})</b> · {sel.reglas_version} · {TEMAS[sel.tema] || ""} · <span className={"tag ev-" + sel.estado_evidencia}>evidencia {txt(sel.estado_evidencia)}</span></p>
              <p className="leyenda">Basado únicamente en {sel.base}. Primer registro {horaPA(sel.fecha_primera)} · último {horaPA(sel.fecha_ultima)}.</p>
              {sel.alertas?.map((a) => <p key={a} className="aviso">⚠ {a}</p>)}
              <h3>Qué se reporta</h3><p>{sel.reporta || sel.titulo}</p>
              <h3>Quién lo reporta</h3><p>{sel.reportado_por?.join(" · ") || sel.ids_fuente.join(", ")} — <b>{sel.fuentes_independientes}</b> procedencia(s) independiente(s) de {sel.registros} titular(es).</p>
              <h3>Qué está respaldado</h3>
              <ul>{sel.citas.map((c, i) => <li key={i}><span className={"tipo t-" + c.tipo}>{c.tipo}</span> {c.afirmacion} <Citas citas={[c]} /></li>)}</ul>
              {sel.contexto?.length > 0 && <><h3>Contexto oficial</h3><ul>{sel.contexto.map((c) => <li key={c.id_evidencia}>{c.texto} <Citas citas={[{ id_evidencia: c.id_evidencia, campo: c.tipo === "indicador" ? "valor" : "magnitude" }]} /><br /><small className="faltante">{c.limitacion}</small></li>)}</ul></>}
              {sel.contradicciones?.length > 0 && <><h3>Versiones incompatibles</h3>{sel.contradicciones.map((k) => <ul key={k.magnitud}>{k.versiones.map((v) => <li key={v.id}><b>{v.valor}</b> según {v.medio}: «{v.titulo}» <code>{v.id}</code></li>)}<li className="faltante">{k.nota}</li></ul>)}</>}
              <h3>Qué falta comprobar</h3><ul>{sel.faltante.map((x) => <li key={x} className="faltante">{x}</li>)}</ul>
              <h3>Acción recomendada</h3><p><b>{sel.accion || "Revisar evidencia."}</b></p>
              <h3>Puntaje desglosado</h3><Barras f={sel} />
              {sel.noticias?.length > 0 && <details><summary>Titulares agrupados ({sel.noticias.length})</summary>
                <table className="tabla"><thead><tr><th>ID</th><th>Medio</th><th>Procedencia</th><th>Publicación</th><th>Detección</th></tr></thead>
                  <tbody>{sel.noticias.map((n) => <tr key={n.id}><td><a href={n.url} target="_blank" rel="noreferrer">{n.id}</a></td><td>{n.medio}</td><td>{n.procedencia}</td><td>{horaPA(n.fecha_publicacion)}</td><td>{horaPA(n.fecha_deteccion)}</td></tr>)}</tbody></table>
              </details>}

              <h2><span className="n">4</span> Borrador con citas</h2>
              <button onClick={draft} disabled={busy}>{busy ? "Generando…" : sel.borrador ? "Regenerar borrador" : "Generar borrador"}</button>
              {sel.borrador && <Borrador b={sel.borrador} />}

              <h2><span className="n">5</span> Revisión humana</h2>
              <p>Estado actual: <b>{txt(sel.estado_revision)}</b></p>
              <input value={revisor} onChange={(e) => setRevisor(e.target.value)} placeholder="Persona revisora (obligatorio)" />
              <textarea value={coment} onChange={(e) => setComent(e.target.value)} placeholder="Comentario: corrección, motivo de descarte o evidencia pedida" rows={2} />
              <div className="estados">{ESTADOS.map((s) => <button key={s} className={sel.estado_revision === s ? "on" : ""} onClick={() => review(s)}>{txt(s)}</button>)}</div>
              <p className="nota">Aprobar como borrador NO publica nada. Con evidencia insuficiente no se puede aprobar.</p>
              {sel.revisiones?.length > 0 && <ul className="hist">{sel.revisiones.map((r, i) => <li key={i}>{horaPA(r.ts)} · <b>{r.revisor}</b> → {txt(r.estado)}{r.comentario && `: ${r.comentario}`}</li>)}</ul>}
            </article>
          )}
        </section>
      </div>
      <Evaluacion ev={ev} />
    </main>
  );
}
