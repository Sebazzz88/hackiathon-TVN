import { useEffect, useState } from "react";
import { api, horaPA } from "../lib.js";

export default function Evaluacion({ irAFicha }) {
  const [ev, setEv] = useState(null);
  useEffect(() => { api("/eval").then(setEv).catch(() => setEv({})); }, []);
  const e = ev?.evaluacion || {};
  const a = ev?.agente || {};

  return (
    <div className="evaluacion">
      <p className="kicker">Etapa 4 · Pruebas</p>
      <h1>Agente frente a baseline</h1>
      {a.agente && (
        <p className="nota">
          {a.agente} · embeddings {a.embeddings === "fastembed" ? "multilingües locales (ONNX)" : "de respaldo léxico"} ·
          {" "}{a.noticias} titulares → {a.eventos} eventos · pipeline {a.segundos_pipeline} s
        </p>
      )}
      {e.disponible === false || !e.metricas ? (
        <p className="vacio">Aún no hay resultados. Corre <code>backend\.venv\Scripts\python eval\run_eval.py</code>.</p>
      ) : (
        <>
          <p className="aviso">
            Ejecución {horaPA(e.generado_utc)} · {e.conjunto}. {e.etiquetas}
          </p>
          <table className="tabla metricas">
            <thead><tr><th>Métrica</th><th className="num">Agente (IA)</th><th className="num">Baseline</th><th>Nota</th></tr></thead>
            <tbody>
              {e.metricas.map((m) => (
                <tr key={m.nombre}>
                  <td>{m.nombre}</td>
                  <td className="num"><b>{String(m.agente)}</b></td>
                  <td className="num">{m.baseline ?? "—"}</td>
                  <td className="nota">{m.nota}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {e.ranking && (
            <div className="comparacion">
              <Top titulo="Top 5 del agente" items={e.ranking.top5_agente} irAFicha={irAFicha} />
              <Top titulo="Baseline: más reciente primero" items={e.ranking.top5_baseline_fecha} irAFicha={irAFicha} />
            </div>
          )}
          <p className="nota">{e.ranking?.nota}</p>
        </>
      )}
    </div>
  );
}

function Top({ titulo, items, irAFicha }) {
  return (
    <section className="bloque">
      <h3 className="kicker">{titulo}</h3>
      <ol className="top">
        {items.map(([id, t]) => <li key={id}><button className="enlace" onClick={() => irAFicha(id)}>{t}</button></li>)}
      </ol>
    </section>
  );
}
