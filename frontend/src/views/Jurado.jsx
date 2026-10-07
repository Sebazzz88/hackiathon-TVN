import { useEffect, useState } from "react";
import { api, cancelado, horaPA } from "../lib.js";

const PREGUNTAS = [
  { q: "«Muéstrame de dónde proviene esta cifra y de qué año es»", ir: "#/ficha/EV-G226d8217c0/resumen",
    como: "Ficha de S&P → Contexto oficial → abre la cita WB:PAN:…:2024 (país, año, unidad, licencia)." },
  { q: "«Si cinco medios replican la misma agencia, ¿cuántas fuentes independientes cuentas?»", ir: "#/ficha/SINT-S-DUP-001/fuentes?p=1",
    como: "Caso de prueba: 3 notas de EFE en 3 medios = 1 procedencia. En un caso real: S&P, 6 notas = 3 procedencias." },
  { q: "«¿Qué ocurre si no hay evidencia?»", ir: "#/consulta?q=" + encodeURIComponent("¿Cuál es la inflación de Panamá hoy?"),
    como: "Abstención explícita: dice qué falta y qué hacer; ninguna cifra inventada." },
  { q: "«¿Y si una fuente intenta cambiar sus instrucciones?»", ir: "#/ficha/SINT-S-INY-001/resumen?p=1",
    como: "La fuente queda marcada, con evidencia 0, y el validador elimina lo que la cite." },
  { q: "«Muéstrame una decisión, una prueba fallida y su corrección»", ir: null,
    como: "Decisión D06 (docs/09_DECISIONS.md) y la prueba T05 que falló y se corrigió con D08 (docs/10_CHANGELOG.md)." },
];

function Metricas({ m }) {
  if (!m) return <p className="vacio">Cargando métricas…</p>;
  if (m.disponible === false) return <p className="vacio">{m.detalle}</p>;
  const nd = (x, v) => (x ? <><b>{x.num}</b>/{x.den} <span className="nota">({Math.round((100 * x.num) / x.den)}%)</span></> : (v ?? "—"));
  return (
    <>
      <p className="nota">Leído de <code>eval/results.json</code> · ejecución {horaPA(m.generado_utc)} · {m.conjunto}. {m.etiquetas}</p>
      <table className="tabla metricas">
        <thead><tr><th>Métrica</th><th className="num">Agente (IA)</th><th className="num">Baseline</th><th>Nota</th></tr></thead>
        <tbody>
          {m.tabla.map((t) => (
            <tr key={t.metrica}><td>{t.metrica}</td><td className="num">{nd(t.agente_nd, String(t.agente))}</td>
              <td className="num">{nd(t.baseline_nd, t.baseline)}</td><td className="nota">{t.nota}</td></tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

/** Pantalla para el jurado: pruebas T01–T10 en vivo, métricas leídas de eval/results.json y respuestas a sus preguntas. */
export default function Jurado() {
  const [inf, setInf] = useState(null);
  const [corriendo, setCorriendo] = useState(false);
  const [seg, setSeg] = useState(0);
  const [met, setMet] = useState(null);
  const [val, setVal] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const ac = new AbortController();
    api("/jurado/pruebas", "GET", undefined, ac.signal).then(setInf).catch((e) => !cancelado(e) && setError(e.message));
    api("/jurado/metricas", "GET", undefined, ac.signal).then(setMet).catch((e) => !cancelado(e) && setMet({ disponible: false, detalle: e.message }));
    api("/validador", "GET", undefined, ac.signal).then(setVal).catch(() => {});
    return () => ac.abort();
  }, []);
  useEffect(() => {
    if (!corriendo) return;
    setSeg(0);
    const t = setInterval(() => setSeg((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, [corriendo]);

  const correr = () => {
    setCorriendo(true); setError("");
    api("/jurado/pruebas", "POST")
      .then((x) => { if (x.en_curso) setError(x.detalle); else setInf(x); })
      .catch((e) => setError(e.message))
      .finally(() => setCorriendo(false));
  };

  return (
    <div className="jurado">
      <p className="kicker">Modo jurado</p>
      <h1>Pruebas de aceptación T01–T10, en vivo</h1>
      <div className="barra-accion">
        <button className="primario" onClick={correr} disabled={corriendo}>{corriendo ? `Corriendo pruebas… ${seg} s` : "Correr T01–T10 ahora"}</button>
        {inf?.generado_utc && !corriendo && (
          <span className="nota">Última ejecución {horaPA(inf.generado_utc)} · {inf.segundos} s · <b>{inf.verdes}/{inf.total} en verde</b></span>
        )}
      </div>
      <p className="nota">Ejecuta <code>pytest tests/test_reto.py</code> en este equipo, sin internet, sin IA externa y con una base temporal.</p>
      {error && <div className="error-caja" role="alert"><p>{error}</p></div>}
      {inf?.disponible === false && !corriendo && <p className="vacio">Aún no se han corrido las pruebas en este equipo. Pulsa el botón.</p>}

      {inf?.filas && (
        <ol className="pruebas-jurado">
          {inf.filas.map((f) => (
            <li key={f.id} className={"prueba-j " + f.estado}>
              <div className="pj-cab">
                <span className="pj-estado" aria-label={f.estado === "verde" ? "aprobada" : "fallida"}>{f.estado === "verde" ? "✓" : "✕"}</span>
                <b>{f.id}</b> {f.titulo}
              </div>
              <p className="pj-esperado"><span className="nota">Esperado:</span> {f.esperado}</p>
              <details>
                <summary>Evidencia: {f.pruebas.length} prueba{f.pruebas.length === 1 ? "" : "s"} automatizada{f.pruebas.length === 1 ? "" : "s"}</summary>
                <ul>
                  {f.pruebas.map((p) => (
                    <li key={p.prueba} className={p.ok ? "" : "pj-falla"}>
                      <code>{p.prueba}</code> · {p.segundos} s · {p.comprueba}
                      {p.mensaje && <pre>{p.mensaje}</pre>}
                    </li>
                  ))}
                  {f.motivo && <li className="pj-falla">{f.motivo}</li>}
                </ul>
              </details>
            </li>
          ))}
        </ol>
      )}

      <section className="bloque">
        <h2>Agente frente a baseline</h2>
        <Metricas m={met} />
        {val && val.emitidas > 0 && (
          <p className="nota">Validador de citas (acumulado en este equipo): {val.emitidas} afirmaciones revisadas · {val.validas} válidas ·
            {" "}{val.eliminadas} eliminadas{Object.keys(val.por_codigo || {}).length > 0 && ` (${Object.entries(val.por_codigo).map(([k, n]) => `${n} ${k.replaceAll("_", " ")}`).join(", ")})`}.</p>
        )}
      </section>

      <section className="bloque">
        <h2>Preguntas del jurado</h2>
        <ul className="preguntas-jurado">
          {PREGUNTAS.map((p) => (
            <li key={p.q}><b>{p.q}</b><br /><span className="nota">{p.como}</span>{p.ir && <> <a href={p.ir}>Mostrar →</a></>}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
