import { useEffect, useRef, useState } from "react";
import { api, COMPONENTES, EVIDENCIA, TEMAS, estadoTxt, hace } from "../lib.js";
import Ficha from "./Ficha.jsx";

export default function Agenda({ corte, ficha, seccion, irAFicha }) {
  const [items, setItems] = useState([]);
  const [limite, setLimite] = useState(5);
  const [sint, setSint] = useState(false);
  const [sel, setSel] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

  const cargar = () =>
    api(`/inbox?limit=${limite}&sinteticos=${sint}`)
      .then((d) => { setItems(d); setCargando(false); })
      .catch((e) => { setError(e.message); setCargando(false); });

  useEffect(() => { cargar(); }, [limite, sint]);

  const detalle = useRef(null);
  const cargarFicha = (id, desplazar = false) => api("/fichas/" + id)
    .then((f) => {
      setSel(f);
      if (f.sintetico && !sint) setSint(true);  // un caso de prueba se ve junto a los demás casos de prueba
      if (desplazar && window.innerWidth < 960) detalle.current?.scrollIntoView({ behavior: "smooth" });
    })
    .catch((e) => setError(e.message));

  // La ficha abierta vive en la URL (#/ficha/<id>/<seccion>); sin ficha en la URL se abre la primera de la lista.
  useEffect(() => { if (ficha) cargarFicha(ficha, true); }, [ficha]);
  useEffect(() => { if (!ficha && items.length) cargarFicha(items[0].id_caso); }, [items, ficha]);

  const actualizar = (f) => { setSel(f); cargar(); };

  return (
    <div className="agenda">
      <section className="lista" aria-label="Agenda priorizada">
        <div className="lista-cab">
          <div>
            <p className="kicker">{sint ? "Casos de prueba controlados" : "Agenda de Panamá"}</p>
            <h1>{sint ? "Casos sintéticos" : `Top ${limite} para revisar`}</h1>
          </div>
          <div className="segmentos" role="group" aria-label="Cantidad">
            {[5, 10, 30].map((n) => (
              <button key={n} className={limite === n ? "seg on" : "seg"} onClick={() => setLimite(n)}>{n}</button>
            ))}
          </div>
        </div>
        <label className="interruptor">
          <input type="checkbox" checked={sint} onChange={(e) => setSint(e.target.checked)} />
          <span>Ver casos de prueba (inyección, contradicciones, recirculada, agencia replicada)</span>
        </label>

        {error && <p className="error">{error}</p>}
        {cargando && <p className="vacio">Cargando agenda…</p>}

        <ol className="items">
          {items.map((f, k) => (
            <li key={f.id_caso}>
              <button className={"item" + (sel?.id_caso === f.id_caso ? " activo" : "")} onClick={() => irAFicha(f.id_caso)}>
                <span className="rank">{k + 1}</span>
                <span className="item-cuerpo">
                  <span className="kicker">
                    {TEMAS[f.tema] || "—"} · {hace(f.fecha_ultima, corte)}
                    {f.sintetico && <em className="sint"> · sintético</em>}
                  </span>
                  <span className="titular">{f.titulo}</span>
                  <span className="meta">
                    <i className={"punto ev-" + f.estado_evidencia} aria-hidden="true" />
                    {EVIDENCIA[f.estado_evidencia]} · {f.fuentes_independientes} fuente{f.fuentes_independientes === 1 ? "" : "s"} indep.
                    {f.registros > 1 && ` · ${f.registros} titulares`}
                    {f.estado_revision !== "nuevo" && <> · <b>{estadoTxt(f.estado_revision)}</b></>}
                  </span>
                  <span className="mini" aria-hidden="true">
                    {COMPONENTES.map(([c, , w]) => <i key={c} className={"c-" + c} style={{ width: `${f.componentes[c] * w}%` }} />)}
                  </span>
                </span>
                <span className={"puntaje banda-" + f.banda} title={`Puntaje de atención ${f.puntaje}/100 (${f.banda})`}>
                  {Math.round(f.puntaje)}
                </span>
              </button>
            </li>
          ))}
        </ol>
        <p className="nota">
          El puntaje ordena la atención (P = 30R + 25I + 20U + 15N + 10E); no es probabilidad de verdad.
          La evidencia se evalúa aparte.
        </p>
      </section>

      <section className="detalle" aria-label="Ficha del tema" ref={detalle}>
        {sel ? <Ficha f={sel} corte={corte} seccion={seccion} onSeccion={(s) => irAFicha(sel.id_caso, s)} onCambio={actualizar} />
          : <p className="vacio">Selecciona un tema.</p>}
      </section>
    </div>
  );
}
