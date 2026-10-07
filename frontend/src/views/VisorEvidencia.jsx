import { useEffect, useRef, useState } from "react";
import { ETIQUETAS, TIPOS_EV, suscribirEvidencia } from "../evidencia.js";
import { api, cancelado, horaPA } from "../lib.js";

const esFecha = (k) => k.startsWith("fecha_") || k === "time";

function Valor({ k, v }) {
  if (v === null || v === undefined || v === "") return <span className="nota">sin dato</span>;
  if (esFecha(k) && typeof v === "string" && v.includes("T")) return <>{horaPA(v)} <span className="nota">(hora de Panamá)</span></>;
  if (k === "url") return <a href={v} target="_blank" rel="noreferrer">{v}</a>;
  return <>{String(v)}</>;
}

/** Panel lateral con el registro FUENTE de una cita: lo que dice el corpus, sin interpretación. Se abre desde cualquier cita. */
export default function VisorEvidencia() {
  const [abierto, setAbierto] = useState(null);   // { id, campo }
  const [reg, setReg] = useState(null);
  const [error, setError] = useState("");
  const cerrar = useRef(null);

  useEffect(() => suscribirEvidencia((x) => { setAbierto(x); setReg(null); setError(""); }), []);

  useEffect(() => {
    if (!abierto) return;
    const ac = new AbortController();
    api("/evidencia/" + abierto.id, "GET", undefined, ac.signal)
      .then(setReg)
      .catch((e) => { if (!cancelado(e)) setError(e.message); });
    return () => ac.abort();
  }, [abierto]);

  useEffect(() => {
    if (!abierto) return;
    const previo = document.activeElement;
    cerrar.current?.focus();
    const tecla = (e) => { if (e.key === "Escape") setAbierto(null); };
    window.addEventListener("keydown", tecla);
    return () => { window.removeEventListener("keydown", tecla); previo?.focus?.(); };
  }, [abierto]);

  if (!abierto) return null;
  return (
    <div className="visor-fondo" onClick={() => setAbierto(null)}>
      <aside className="visor" role="dialog" aria-modal="true" aria-label="Registro fuente de la cita" onClick={(e) => e.stopPropagation()}>
        <header className="visor-cab">
          <div>
            <p className="kicker">Registro fuente de la cita</p>
            <h2>{reg ? TIPOS_EV[reg.tipo] || reg.tipo : "Cargando…"}</h2>
          </div>
          <button ref={cerrar} className="visor-cerrar" onClick={() => setAbierto(null)} aria-label="Cerrar">✕</button>
        </header>

        <p className="visor-id">Evidencia <b>{abierto.id}</b>{abierto.campo && <> · campo citado: <b>{ETIQUETAS[abierto.campo] || abierto.campo}</b></>}</p>

        {error && <div className="error-caja" role="alert"><p>{error}</p><p className="nota">Esta cita no se puede comprobar en el corpus: no debería haberse emitido.</p></div>}
        {!reg && !error && <p className="vacio">Buscando en el corpus…</p>}
        {reg && (
          <>
            {reg.sintetico && <p className="aviso">Caso sintético de prueba: este registro no es una noticia real.</p>}
            <dl className="visor-campos">
              {Object.entries(reg.campos).map(([k, v]) => (
                <div key={k} className={"visor-fila" + (k === abierto.campo ? " citado" : "")}>
                  <dt>{ETIQUETAS[k] || k}{k === abierto.campo && <span className="visor-marca">citado</span>}</dt>
                  <dd><Valor k={k} v={v} /></dd>
                </div>
              ))}
            </dl>
            {reg.nota && <p className="nota">{reg.nota}</p>}
            {reg.url && <a className="visor-abrir" href={reg.url} target="_blank" rel="noreferrer">Abrir la fuente original ↗</a>}
          </>
        )}
      </aside>
    </div>
  );
}
