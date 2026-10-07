// Piezas compartidas para mostrar afirmaciones con su tipo y sus citas (ficha, borrador y consulta).
import { TIPOS } from "../lib.js";
import { ETIQUETAS, abrirEvidencia } from "../evidencia.js";

/** Cita clicable: abre el registro fuente de la evidencia con el campo citado resaltado. */
export function Cita({ id, campo }) {
  return (
    <button type="button" className="cita" title={`Abrir el registro fuente de ${id} (campo ${campo})`}
      onClick={() => abrirEvidencia(id, campo)}>
      {id} · {ETIQUETAS[campo] || campo}
    </button>
  );
}

export function Tipo({ t }) {
  return <span className={"tipo t-" + t}>{TIPOS[t] || t}</span>;
}

/** Afirmaciones ya validadas: tipo, texto y cada una de sus citas. */
export function Afirmaciones({ lista }) {
  if (!lista.length) return <p className="nota">Sin afirmaciones respaldadas para esta sección.</p>;
  return (
    <ul className="afirmaciones">
      {lista.map((a, i) => (
        <li key={i}><Tipo t={a.tipo} /> <span>{a.texto}</span> {a.citas.map((c, j) => <Cita key={j} id={c.id_evidencia} campo={c.campo} />)}</li>
      ))}
    </ul>
  );
}

/** Lo que el validador descartó, a la vista y tachado, con el motivo de cada eliminación. */
export function Eliminadas({ lista, resumen }) {
  if (!lista?.length) return null;
  return (
    <details className="eliminadas">
      <summary>{resumen}</summary>
      <ul>{lista.map((e, i) => <li key={i}><s>{e.texto}</s> <span className="nota">— {e.motivo}</span></li>)}</ul>
    </details>
  );
}
