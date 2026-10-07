/** Tabla agente vs baseline (pestañas Evaluación y Modo jurado). Si la fila trae numerador/denominador, se muestran
 *  separados y con su porcentaje; si no, el valor tal como lo calculó eval/run_eval.py. */
function Valor({ nd, v, destacar }) {
  if (nd) return <><b>{nd.num}</b>/{nd.den} <span className="nota">({Math.round((100 * nd.num) / nd.den)}%)</span></>;
  const txt = v === null || v === undefined ? "—" : String(v);
  return destacar ? <b>{txt}</b> : txt;
}

export default function TablaMetricas({ filas }) {
  return (
    <table className="tabla metricas">
      <thead><tr><th>Métrica</th><th className="num">Agente (IA)</th><th className="num">Baseline</th><th>Nota</th></tr></thead>
      <tbody>
        {filas.map((t) => (
          <tr key={t.metrica}>
            <td>{t.metrica}</td>
            <td className="num"><Valor nd={t.agente_nd} v={t.agente} destacar /></td>
            <td className="num"><Valor nd={t.baseline_nd} v={t.baseline} /></td>
            <td className="nota">{t.nota}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
