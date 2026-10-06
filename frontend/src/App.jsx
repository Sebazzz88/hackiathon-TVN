import { useEffect, useState } from "react";

async function api(path, method = "GET", body) {
  const r = await fetch("/api" + path, { method, headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(typeof d.detail === "string" ? d.detail : "Error " + r.status);
  return d;
}
const ESTADOS = ["nuevo", "en_revision", "requiere_evidencia", "aprobado_como_borrador", "descartado"];
const txt = (s) => s.replaceAll("_", " ");

export default function App() {
  const [items, setItems] = useState([]);
  const [sel, setSel] = useState(null);
  const [q, setQ] = useState("");
  const [ans, setAns] = useState(null);
  const [revisor, setRevisor] = useState("");
  const [msg, setMsg] = useState("");
  const fail = (e) => setMsg(e.message);
  const load = () => api("/inbox?limit=5").then(setItems).catch(fail);
  useEffect(() => { load(); }, []);

  const open = (id) => { setMsg(""); api("/fichas/" + id).then(setSel).catch(fail); };
  const draft = () => api(`/fichas/${sel.id_caso}/draft`, "POST").then(setSel).catch(fail);
  const review = (estado) => api(`/fichas/${sel.id_caso}/review`, "POST", { estado, revisor, comentario: "" })
    .then((f) => { setSel(f); setMsg(""); load(); }).catch(fail);
  const ask = () => { setMsg(""); api("/query", "POST", { pregunta: q }).then(setAns).catch(fail); };

  return (
    <main>
      <h1>Qué temas revisar hoy</h1>
      {msg && <p className="alerta" role="alert">{msg}</p>}
      <div className="cols">
        <section>
          <div className="consulta">
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Pregunta sobre el corpus, en español" onKeyDown={(e) => e.key === "Enter" && ask()} />
            <button onClick={ask}>Consultar</button>
          </div>
          {ans && (
            <div className="resp">
              {ans.abstencion ? <b>No hay evidencia suficiente para responder.</b> : <p>{ans.respuesta}</p>}
              {ans.faltante.map((f) => <p key={f} className="faltante">Falta: {f}</p>)}
              {ans.citas.map((c, i) => <p key={i} className="cita">[{c.tipo}] {c.afirmacion} — {c.id_evidencia}, {c.campo}</p>)}
            </div>
          )}
          <h2>Bandeja priorizada</h2>
          {items.map((f) => (
            <button key={f.id_caso} className={"fila" + (sel?.id_caso === f.id_caso ? " activa" : "")} onClick={() => open(f.id_caso)}>
              <span className="pts">{f.puntaje}</span>
              <span className="tit">{f.titulo}{f.sintetico && " (dato sintético)"}</span>
              <span className={"tag ev-" + f.estado_evidencia}>evidencia {txt(f.estado_evidencia)}</span>
              <span className="tag">{f.banda}</span>
            </button>
          ))}
        </section>

        <section>
          {!sel ? <p className="vacio">Abre un tema de la bandeja para ver su ficha.</p> : (
            <article>
              <h2>{sel.titulo}</h2>
              <p>Puntaje {sel.puntaje}/100 ({sel.banda}) · {sel.reglas_version} · basado únicamente en {sel.base}</p>
              <p className="comp">{Object.entries(sel.componentes).map(([k, v]) => `${k} ${v}`).join("  ·  ")}</p>
              <p>Estado de evidencia: <b>{txt(sel.estado_evidencia)}</b> · Revisión: <b>{txt(sel.estado_revision)}</b></p>
              {sel.faltante.length > 0 && <><h3>Qué falta comprobar</h3><ul>{sel.faltante.map((x) => <li key={x}>{x}</li>)}</ul></>}
              {sel.citas.length > 0 && <><h3>Citas</h3><ul>{sel.citas.map((c, i) => <li key={i}>[{c.tipo}] {c.afirmacion} — {c.id_evidencia}, {c.campo}</li>)}</ul></>}
              <button onClick={draft}>Generar borrador</button>
              {sel.borrador && <pre>{JSON.stringify(sel.borrador, null, 2)}</pre>}
              <h3>Revisión humana</h3>
              <input value={revisor} onChange={(e) => setRevisor(e.target.value)} placeholder="Nombre de la persona revisora" />
              <div className="estados">{ESTADOS.map((s) => <button key={s} onClick={() => review(s)}>{txt(s)}</button>)}</div>
              <p className="nota">Aprobar como borrador no publica nada.</p>
            </article>
          )}
        </section>
      </div>
    </main>
  );
}
