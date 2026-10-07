import { COMPONENTES, EVIDENCIA, TEMAS, estadoTxt, fechasNota, hace, textoProcedencia } from "../lib.js";
import { SECCIONES } from "../rutas.js";
import Borrador from "./Borrador.jsx";
import { Cita, Tipo } from "./Citas.jsx";
import Revision from "./Revision.jsx";

export default function Ficha({ f, corte, seccion, onSeccion, onCambio }) {
  const sec = Object.hasOwn(SECCIONES, seccion) ? seccion : "resumen";

  return (
    <article className="ficha">
      <header className="ficha-cab">
        <p className="kicker">
          {TEMAS[f.tema] || "Tema"} · {hace(f.fecha_ultima, corte)} · {f.id_caso}
          {f.sintetico && <em className="sint"> · caso sintético de prueba</em>}
        </p>
        <h2>{f.titulo}</h2>
        <div className="sellos">
          <span className={"sello banda-" + f.banda}><b>{Math.round(f.puntaje)}</b>/100 · prioridad {f.banda}</span>
          <span className={"sello ev ev-" + f.estado_evidencia}><i className={"punto ev-" + f.estado_evidencia} />{EVIDENCIA[f.estado_evidencia]}</span>
          <span className="sello sello-proc">{textoProcedencia(f)}</span>
          <span className="sello">{estadoTxt(f.estado_revision)}</span>
        </div>
        <p className="banner-metadatos" role="note">Basado únicamente en titular/metadatos: no se leyó ningún artículo completo.</p>
      </header>

      {f.alertas?.length > 0 && (
        <ul className="alertas">{f.alertas.map((a) => <li key={a}>{a}</li>)}</ul>
      )}

      <nav className="subtabs" aria-label="Secciones de la ficha">
        {Object.entries(SECCIONES).map(([k, t]) => (
          <button key={k} className={sec === k ? "subtab on" : "subtab"} onClick={() => onSeccion(k)}>
            {t}{k === "borrador" && f.borrador && <i className="ok" aria-label="generado" />}
          </button>
        ))}
      </nav>

      {sec === "resumen" && <Resumen f={f} />}
      {sec === "fuentes" && <Fuentes f={f} />}
      {sec === "puntaje" && <Puntaje f={f} />}
      {sec === "borrador" && <Borrador f={f} onCambio={onCambio} />}
      {sec === "revision" && <Revision f={f} onCambio={onCambio} />}
    </article>
  );
}

function Bloque({ titulo, children }) {
  return (
    <section className="bloque">
      <h3 className="kicker">{titulo}</h3>
      {children}
    </section>
  );
}

function Resumen({ f }) {
  const titulares = f.citas.filter((c) => c.tipo !== "hecho");
  return (
    <div className="panel">
      <Bloque titulo="Qué se reporta"><p className="lead">{f.titulo}</p></Bloque>
      <Bloque titulo="Quién lo reporta">
        <p className="proc-resumen"><b>{textoProcedencia(f)}</b></p>
        {f.procedencias?.length > 0 ? (
          <ul className="proc-lista">
            {f.procedencias.map((p) => (
              <li key={p.etiqueta}>
                <b>{p.nombre}</b> · {p.notas} nota{p.notas === 1 ? "" : "s"}
                {p.medios.length > 1 && <span className="nota"> (replicada por {p.medios.filter((m) => m !== p.nombre).join(", ")})</span>}
              </li>
            ))}
          </ul>
        ) : <p>{f.reportado_por?.join(" · ")}</p>}
        <p className="nota">La repetición no es corroboración: mismo dominio o misma agencia citada = una sola procedencia.</p>
      </Bloque>
      <Bloque titulo="Qué está respaldado">
        <ul className="respaldos">
          {titulares.length === 0 && <li className="pendiente">Nada todavía: la única fuente no es confiable o no aporta evidencia.</li>}
          {titulares.slice(0, 5).map((c, i) => <li key={i}><Tipo t={c.tipo} /> {c.afirmacion} <Cita id={c.id_evidencia} campo={c.campo} /></li>)}
          {titulares.length > 5 && <li className="nota">… y {titulares.length - 5} titulares más en la pestaña Fuentes.</li>}
        </ul>
      </Bloque>
      {f.contexto?.length > 0 && (
        <Bloque titulo="Contexto oficial">
          <ul className="respaldos">
            {f.contexto.map((c) => (
              <li key={c.id_evidencia}>
                <Tipo t="hecho" /> {c.texto} <Cita id={c.id_evidencia} campo={c.tipo === "indicador" ? "valor" : "magnitude"} />
                <small className="limite">{c.limitacion}</small>
              </li>
            ))}
          </ul>
        </Bloque>
      )}
      {f.contradicciones?.length > 0 && (
        <Bloque titulo="Versiones incompatibles">
          {f.contradicciones.map((k) => (
            <div key={k.magnitud} className="versiones">
              {k.versiones.map((v) => (
                <div key={v.id} className="version">
                  <span className="kicker">{v.medio}</span>
                  <p>{v.titulo}</p>
                  <Cita id={v.id} campo="titulo" />
                </div>
              ))}
              <p className="nota">{k.nota}</p>
            </div>
          ))}
        </Bloque>
      )}
      <Bloque titulo="Qué falta comprobar">
        <ul className="pendientes">{f.faltante.map((x) => <li key={x}>{x}</li>)}</ul>
      </Bloque>
      <Bloque titulo="Acción recomendada"><p className="accion">{f.accion}</p></Bloque>
    </div>
  );
}

function Fuentes({ f }) {
  const grupos = {};
  for (const n of f.noticias || []) (grupos[n.procedencia] ||= []).push(n);
  return (
    <div className="panel">
      <p className="nota">
        {textoProcedencia(f)}. Horas en hora de Panamá.
        GDELT no informa fecha de publicación: se muestra la de detección.
      </p>
      {Object.entries(grupos).map(([proc, ns]) => (
        <div key={proc} className="procedencia">
          <h4>{proc.replace("medio:", "").replace("agencia:", "Agencia ").replace("replica:", "Réplica de ")}
            {ns.length > 1 && <span className="nota"> · {ns.length} titulares = 1 fuente</span>}</h4>
          <ul>
            {ns.map((n) => (
              <li key={n.id} className={n.inyeccion_detectada ? "inyectada" : ""}>
                <a href={n.url} target="_blank" rel="noreferrer">{n.titulo}</a>
                <span className="meta">
                  {n.medio} · {fechasNota(n)}
                  {n.recirculada && " · publicación antigua"}{n.inyeccion_detectada && " · posible inyección (no confiable)"} · <Cita id={n.id} campo="titulo" />
                </span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

function Puntaje({ f }) {
  return (
    <div className="panel">
      <div className="puntaje-grande">
        <span className={"cifra banda-" + f.banda}>{Math.round(f.puntaje)}</span>
        <span>
          <b>Prioridad {f.banda}</b><br />
          <small>P = 30R + 25I + 20U + 15N + 10E · {f.reglas_version} · bajo [0,40) medio [40,70) alto [70,100]</small>
        </span>
      </div>
      <table className="componentes explicado">
        <thead>
          <tr><th>Componente</th><th>Valor 0–1</th><th className="num">Peso</th><th className="num">Aporte</th></tr>
        </thead>
        <tbody>
          {COMPONENTES.map(([k, nombre, peso]) => (
            <tr key={k}>
              <th scope="row">
                <b>{k}</b> {nombre}
                <span className="porque">{f.justificacion?.[k]}</span>
              </th>
              <td className="barra-celda">
                <span className="barra" role="img" aria-label={`${nombre}: ${f.componentes[k].toFixed(2)} de 1`}>
                  <i className={"c-" + k} style={{ width: `${f.componentes[k] * 100}%` }} />
                </span>
                <span className="valor01">{f.componentes[k].toFixed(2)}</span>
              </td>
              <td className="num">×{peso}</td>
              <td className="num"><b>{(f.componentes[k] * peso).toFixed(1)}</b> pts</td>
            </tr>
          ))}
          <tr className="total">
            <th scope="row">Total</th><td /><td className="num">100</td><td className="num"><b>{f.puntaje.toFixed(1)}</b> pts</td>
          </tr>
        </tbody>
      </table>
      <p className="nota">Para ver cómo cambiaría el ranking con otros pesos, usa <b>«¿Qué pasaría si…?»</b> en la agenda (no guarda nada).</p>
      <p className="nota">
        El puntaje ordena la atención; no es probabilidad de verdad ni de impacto. Una prioridad alta con evidencia
        insuficiente requiere investigación y no habilita la aprobación.
      </p>
    </div>
  );
}
