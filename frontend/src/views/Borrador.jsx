import { useState } from "react";
import { api } from "../lib.js";
import { Cita, Tipo } from "./Ficha.jsx";

export default function Borrador({ f, onCambio }) {
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState("");
  const b = f.borrador;

  const generar = () => {
    setOcupado(true);
    setError("");
    api(`/fichas/${f.id_caso}/draft`, "POST")
      .then((x) => { onCambio(x); setOcupado(false); })
      .catch((e) => { setError(e.message); setOcupado(false); });
  };

  return (
    <div className="panel">
      <div className="barra-accion">
        <button className="primario" onClick={generar} disabled={ocupado}>
          {ocupado ? "Generando…" : b ? "Regenerar borrador" : "Generar paquete editorial"}
        </button>
        {b?.generador && <span className="nota">Generador: <code>{b.generador}</code>{b.meta_llm?.costo_usd != null && ` · ${b.meta_llm.costo_usd} USD`}</span>}
      </div>
      {error && <p className="error">{error}</p>}
      {!b && !ocupado && (
        <p className="vacio">
          Genera título, enfoque, brief, preguntas, guion y copy. Cada afirmación lleva su cita; un validador elimina lo que
          no esté respaldado.
        </p>
      )}
      {b?.stub && <p className="vacio">{b.brief}</p>}
      {b?.abstencion && <p className="pendiente">{b.faltante?.join(" ")}</p>}
      {b && !b.stub && !b.abstencion && <Paquete b={b} />}
    </div>
  );
}

function Afirmaciones({ lista }) {
  if (!lista.length) return <p className="nota">Sin afirmaciones respaldadas para esta sección.</p>;
  return (
    <ul className="afirmaciones">
      {lista.map((a, i) => (
        <li key={i}><Tipo t={a.tipo} /> <span>{a.texto}</span> {a.citas.map((c, j) => <Cita key={j} id={c.id_evidencia} campo={c.campo} />)}</li>
      ))}
    </ul>
  );
}

function Paquete({ b }) {
  const sec = (s) => b.afirmaciones.filter((a) => a.seccion === s);
  const guionOk = b.guion_segundos_estimados >= 45 && b.guion_segundos_estimados <= 60;
  return (
    <div className="paquete">
      <p className="aviso">{b.aviso}</p>

      <section className="pieza">
        <h3 className="kicker">Título propuesto</h3>
        <p className="titulo-propuesto">{b.titulo}</p>
        {b.enfoque && <p><Tipo t={b.enfoque.tipo} /> {b.enfoque.texto} {b.enfoque.citas.map((c, j) => <Cita key={j} id={c.id_evidencia} campo={c.campo} />)}</p>}
      </section>

      <section className="pieza">
        <h3 className="kicker">Brief <span className={b.brief_palabras <= 250 ? "contador" : "contador mal"}>{b.brief_palabras}/250 palabras</span></h3>
        <p className="leyenda">{b.leyenda}</p>
        <Afirmaciones lista={sec("brief")} />
      </section>

      <section className="pieza dos">
        <div>
          <h3 className="kicker">Preguntas de investigación</h3>
          <ol>{b.preguntas.map((p) => <li key={p}>{p}</li>)}</ol>
        </div>
        <div>
          <h3 className="kicker">Fuentes y verificaciones pendientes</h3>
          <ul className="pendientes">{b.verificaciones_pendientes.map((p) => <li key={p}>{p}</li>)}</ul>
        </div>
      </section>

      <section className="pieza guion">
        <h3 className="kicker">Guion para TV <span className={guionOk ? "contador" : "contador mal"}>~{b.guion_segundos_estimados} s · meta 45–60 s</span></h3>
        {b.guion_aviso && <p className="pendiente">{b.guion_aviso}</p>}
        <Afirmaciones lista={sec("guion")} />
      </section>

      <section className="pieza">
        <h3 className="kicker">Copy digital <span className={b.copy_palabras <= 80 ? "contador" : "contador mal"}>{b.copy_palabras}/80 palabras</span></h3>
        <Afirmaciones lista={sec("copy")} />
      </section>

      <p className="nota">
        Cobertura de citas: {b.cobertura_citas.con_cita_valida}/{b.cobertura_citas.emitidas} afirmaciones con cita válida.
      </p>
      {b.eliminadas?.length > 0 && (
        <details className="eliminadas">
          <summary>{b.eliminadas.length} afirmación(es) eliminadas por el validador</summary>
          <ul>{b.eliminadas.map((e, i) => <li key={i}><s>{e.texto}</s> <span className="nota">— {e.motivo}</span></li>)}</ul>
        </details>
      )}
    </div>
  );
}
