import { useEffect, useState } from "react";
import { api, horaPA } from "../lib.js";

const FUENTES = {
  "noticias.csv": ["Noticias", "TVN RSS (solo título, URL y fecha) + GDELT DOC 2.0"],
  "indicadores.csv": ["Indicadores", "Banco Mundial · 6 países × 6 indicadores × 2010–2024 · CC BY 4.0"],
  "eventos.geojson": ["Sismos", "USGS · 2024 · M ≥ 3 · caja lat 5–12, lon −86/−76"],
};

export default function Datos({ meta }) {
  const [q, setQ] = useState(null);
  useEffect(() => { api("/quality-report").then(setQ).catch(() => setQ({ disponible: false })); }, []);
  const n = q?.noticias || {};

  return (
    <div className="datos">
      <p className="kicker">Etapa 1 · Cargar</p>
      <h1>Reporte de calidad del snapshot</h1>
      <p className="nota">Paquete público congelado. La carga no se bloquea por errores: se separan y se reportan. Los nulos se conservan, nunca se rellenan con cero.</p>

      {q?.disponible === false ? <p className="vacio">Sin reporte: corre <code>python data\scripts\validate.py</code>.</p> : (
        <div className="kpis">
          <Kpi v={n.validas ?? "—"} t="noticias válidas" s={`${n.con_error ?? 0} con error`} />
          <Kpi v={n.tvn_validas ?? "—"} t="de TVN" s="mínimo exigido: 20" />
          <Kpi v={n.medios_distintos ?? "—"} t="medios distintos" />
          <Kpi v={q?.indicadores ? `${q.indicadores.con_valor}/${q.indicadores.celdas}` : "—"} t="celdas Banco Mundial con valor" s={q?.indicadores && `${q.indicadores.nulas} nulas conservadas`} />
          <Kpi v={q?.eventos?.total ?? "—"} t="sismos USGS 2024" s={q?.eventos && `M máx. ${q.eventos.magnitud_max}`} />
        </div>
      )}

      <section className="bloque">
        <h3 className="kicker">Catálogo</h3>
        <table className="tabla">
          <thead><tr><th>Archivo</th><th>Fuente</th><th>Registros</th><th>SHA-256</th></tr></thead>
          <tbody>
            {Object.entries(meta?.archivos || {}).map(([k, v]) => (
              <tr key={k}>
                <td><b>{FUENTES[k]?.[0] || k}</b><br /><code>{k}</code></td>
                <td>{FUENTES[k]?.[1] || "—"}</td>
                <td className="num">{v.registros}</td>
                <td><code title={v.sha256}>{v.sha256.slice(0, 12)}…</code></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="bloque">
        <h3 className="kicker">Cobertura y límites</h3>
        <ul className="pendientes">
          <li>Corte del snapshot: {horaPA(meta?.fecha_corte_UTC)} (hora de Panamá). Rango de noticias: {horaPA(n.cobertura?.desde)} → {horaPA(n.cobertura?.hasta)}.</li>
          <li>{n.sin_fecha_publicacion ?? "—"} registros de GDELT no traen fecha de publicación: se usa la de detección y se indica.</li>
          {meta?.consultas_fallidas > 0 && <li>{meta.consultas_fallidas} de {meta.consultas} consultas a las APIs fallaron por límite de tasa de GDELT; quedan registradas en el manifest.</li>}
          {q?.indicadores?.nota && <li>{q.indicadores.nota}</li>}
          {q?.eventos?.nota && <li>{q.eventos.nota} Solo se usa para hechos sísmicos.</li>}
          <li>{meta?.licencia_condiciones}</li>
        </ul>
      </section>
    </div>
  );
}

function Kpi({ v, t, s }) {
  return <div className="kpi"><b>{v}</b><span>{t}</span>{s && <small>{s}</small>}</div>;
}
