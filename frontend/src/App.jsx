import { Component, useCallback, useEffect, useState } from "react";
import { api, fechaPA, horaPA } from "./lib.js";
import { construir, parsear } from "./rutas.js";
import Agenda from "./views/Agenda.jsx";
import Consulta from "./views/Consulta.jsx";
import Datos from "./views/Datos.jsx";
import Evaluacion from "./views/Evaluacion.jsx";
import Jurado from "./views/Jurado.jsx";
import VisorEvidencia from "./views/VisorEvidencia.jsx";

const VISTAS = [
  ["agenda", "Agenda"],
  ["consulta", "Consultar"],
  ["datos", "Datos"],
  ["evaluacion", "Evaluación"],
  ["jurado", "Modo jurado"],
];

/** Si una vista falla al pintar, se muestra qué hacer en lugar de una pantalla en blanco. */
class Contenedor extends Component {
  state = { error: null };
  static getDerivedStateFromError(error) { return { error }; }
  componentDidCatch(error) { console.error("Error de interfaz:", error); }
  componentDidUpdate(prev) { if (prev.clave !== this.props.clave && this.state.error) this.setState({ error: null }); }
  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="error-caja" role="alert">
        <p><b>Esta vista tuvo un problema al mostrarse.</b> Tus datos no se perdieron.</p>
        <button onClick={() => { window.location.hash = "#/agenda"; this.setState({ error: null }); }}>Volver a la agenda</button>
        <button onClick={() => window.location.reload()}>Recargar la página</button>
      </div>
    );
  }
}

export default function App() {
  const [ruta, setRuta] = useState(() => parsear(window.location.hash));
  const [meta, setMeta] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const f = () => setRuta(parsear(window.location.hash));
    window.addEventListener("hashchange", f);
    return () => window.removeEventListener("hashchange", f);
  }, []);
  useEffect(() => {
    api("/meta").then(setMeta).catch((e) => setError(e.message));
  }, []);

  /** Cambia parte de la ruta conservando el resto (tamaño de lista, casos de prueba...). Es la única forma de navegar. */
  const navegar = useCallback((cambios) => {
    const hash = construir({ ...parsear(window.location.hash), ...cambios });
    if (hash !== window.location.hash) window.location.hash = hash;
  }, []);
  const irAFicha = useCallback((id, seccion = "resumen", opciones = {}) => {
    // Los casos de prueba solo aparecen en su lista: si la ficha es sintética se abre dentro de esa lista.
    navegar({ vista: "agenda", ficha: id, seccion, ...("sint" in opciones ? { sint: opciones.sint } : {}) });
  }, [navegar]);

  const corte = meta?.fecha_corte_UTC;
  const vista = ruta.vista;

  return (
    <div className="app">
      <header className="cabecera">
        <div className="marca">
          <span className="marca-tvn">TVN</span>
          <span className="marca-sep" aria-hidden="true" />
          <span className="marca-txt">Copiloto editorial</span>
        </div>
        <nav className="tabs" aria-label="Secciones">
          {VISTAS.map(([k, t]) => (
            <button key={k} className={vista === k ? "tab on" : "tab"} onClick={() => navegar({ vista: k, ficha: null })}
              aria-current={vista === k ? "page" : undefined}>
              {t}
            </button>
          ))}
        </nav>
        {meta?.ia && (
          <div className={"estado-ia" + (meta.ia.conectado ? " on" : "")}
            title={meta.ia.conectado
              ? `IA generativa: ${meta.ia.modelo} (${meta.ia.local ? "local, gratuita, sin internet" : meta.ia.proveedor}). Embeddings ${meta.ia.embeddings}.`
              : `IA generativa no disponible: ${meta.ia.motivo || "sin configurar"}${meta.ia.respuestas_en_cache ? `. Hay ${meta.ia.respuestas_en_cache} respuestas en caché` : ""}. La IA local de embeddings sí está activa.`}>
            <i className="ia-punto" /> IA {meta.ia.conectado ? `${meta.ia.modelo}${meta.ia.local ? " · local" : ""}` : meta.ia.respuestas_en_cache ? "en caché" : "solo embeddings"}
          </div>
        )}
        <div className="corte" title="Los datos son un snapshot congelado: la urgencia se mide contra esta fecha">
          {corte ? <>Corte <b>{fechaPA(corte)}</b> · {horaPA(corte).split(", ").pop()} PTY</> : "…"}
          {meta?.agent_mode && meta.agent_mode !== "live" && <span className="modo">modo {meta.agent_mode}</span>}
        </div>
      </header>

      {error && <div className="aviso-global" role="alert">{error}</div>}

      <main className="contenido">
        <Contenedor clave={vista}>
          {vista === "agenda" && <Agenda corte={corte} ruta={ruta} navegar={navegar} />}
          {vista === "consulta" && <Consulta inicial={ruta.q} irAFicha={irAFicha} navegar={navegar} />}
          {vista === "datos" && <Datos meta={meta} />}
          {vista === "evaluacion" && <Evaluacion irAFicha={irAFicha} />}
          {vista === "jurado" && <Jurado />}
        </Contenedor>
      </main>

      <VisorEvidencia />

      <footer className="pie">
        Prototipo hackIAthon 2026 · Datos públicos (TVN RSS solo metadatos, GDELT, Banco Mundial, USGS) ·
        Las salidas son borradores para revisión humana: <b>nada se publica automáticamente</b>.
      </footer>
    </div>
  );
}
