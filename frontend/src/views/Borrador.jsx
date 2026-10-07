import { useEffect, useState } from "react";
import { generando, generarBorrador } from "../lib.js";
import { Cita, Tipo } from "./Ficha.jsx";

export default function Borrador({ f, onCambio }) {
  const [ocupado, setOcupado] = useState(() => generando(f.id_caso));
  const [error, setError] = useState("");
  const b = f.borrador;
  const [seg, setSeg] = useState(0);
  useEffect(() => {
    if (!ocupado) return;
    setSeg(0);
    const t = setInterval(() => setSeg((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, [ocupado]);

  // Cada vez que se abre esta ficha: si ya se estaba generando (otra visita), se engancha a esa misma generación.
  useEffect(() => {
    let vivo = true;
    setOcupado(generando(f.id_caso));
    setError("");
    if (generando(f.id_caso)) {
      generarBorrador(f.id_caso)
        .then((x) => { if (vivo) onCambio(x); })
        .catch((e) => { if (vivo) setError(e.message); })
        .finally(() => { if (vivo) setOcupado(false); });
    }
    return () => { vivo = false; };
  }, [f.id_caso]);

  const generar = () => {
    if (generando(f.id_caso)) return;
    setOcupado(true);
    setError("");
    const id = f.id_caso;
    generarBorrador(id)
      .then((x) => onCambio(x))                       // Agenda ignora la respuesta si ya se abrió otra ficha
      .catch((e) => setError(e.message))
      .finally(() => setOcupado(false));
  };

  return (
    <div className="panel">
      <div className="barra-accion">
        <button className="primario" onClick={generar} disabled={ocupado}>
          {ocupado ? `Generando… ${seg} s` : b ? "Regenerar borrador" : "Generar paquete editorial"}
        </button>
        {b?.generador && <Generador b={b} />}
      </div>
      {ocupado && <p className="nota">Si la IA local está activa, el modelo redacta en este equipo; en CPU puede tardar 1–3 minutos. Después queda en caché y sale al instante.</p>}
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

function Generador({ b }) {
  const ia = b.generador.startsWith("llm:") || b.generador.startsWith("cache:");
  const m = b.meta_llm || {};
  return (
    <span className={"generador" + (ia ? " ia" : "")}>
      {ia ? (
        <><i className="ia-punto" /> Redactado por IA · {b.generador.split(":").pop()}
          {b.generador.startsWith("cache:") && " · desde caché"}
          {m.tokens_entrada != null && ` · ${m.tokens_entrada + m.tokens_salida} tokens`}
          {m.costo_usd != null && ` · ${m.costo_usd} USD`}</>
      ) : (
        <>Plantilla sin IA generativa{m.motivo && ` (${m.motivo})`}</>
      )}
    </span>
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
        Validador en código: {b.validador ? `${b.validador.emitidas} afirmaciones emitidas · ${b.validador.validas} válidas · ${b.validador.eliminadas} eliminadas` : `${b.cobertura_citas.con_cita_valida}/${b.cobertura_citas.emitidas} con cita válida`}.
        Cada cita se puede abrir para ver su registro fuente.
      </p>
      {b.eliminadas?.length > 0 && (
        <details className="eliminadas">
          <summary>{b.eliminadas.length} afirmación(es) eliminadas por el validador{b.validador?.por_codigo && ` (${Object.entries(b.validador.por_codigo).map(([k, n]) => `${n} ${k.replaceAll("_", " ")}`).join(", ")})`}</summary>
          <ul>{b.eliminadas.map((e, i) => <li key={i}><s>{e.texto}</s> <span className="nota">— {e.motivo}</span></li>)}</ul>
        </details>
      )}
    </div>
  );
}
