import { useEffect, useState } from "react";
import { api, fechaPA, horaPA } from "./lib.js";
import Agenda from "./views/Agenda.jsx";
import Consulta from "./views/Consulta.jsx";
import Datos from "./views/Datos.jsx";
import Evaluacion from "./views/Evaluacion.jsx";

const VISTAS = [
  ["agenda", "Agenda"],
  ["consulta", "Consultar"],
  ["datos", "Datos"],
  ["evaluacion", "Evaluación"],
];

/** Rutas por hash (sirven como enlaces directos para Notion o el pitch):
 *  #/agenda · #/ficha/<id>/<seccion> · #/consulta?q=<pregunta> · #/datos · #/evaluacion */
function leerRuta() {
  const [ruta, qs] = window.location.hash.replace(/^#\/?/, "").split("?");  // URLSearchParams decodifica (respeta "&")
  const partes = ruta.split("/").filter(Boolean).map(decodeURIComponent);
  const q = new URLSearchParams(qs || "").get("q") || "";
  if (partes[0] === "ficha") return { vista: "agenda", ficha: partes[1], seccion: partes[2] || "resumen", q };
  return { vista: VISTAS.some(([k]) => k === partes[0]) ? partes[0] : "agenda", q };
}

export default function App() {
  const [ruta, setRuta] = useState(leerRuta);
  const [meta, setMeta] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const f = () => setRuta(leerRuta());
    window.addEventListener("hashchange", f);
    return () => window.removeEventListener("hashchange", f);
  }, []);
  useEffect(() => {
    api("/meta").then(setMeta).catch(() => setError("No hay conexión con el backend (http://localhost:8000). ¿Está encendido?"));
  }, []);

  const ir = (hash) => { window.location.hash = hash; };
  const irAFicha = (id, seccion = "resumen") => ir(`/ficha/${id}/${seccion}`);
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
            <button key={k} className={vista === k ? "tab on" : "tab"} onClick={() => ir("/" + k)} aria-current={vista === k}>
              {t}
            </button>
          ))}
        </nav>
        <div className="corte" title="Los datos son un snapshot congelado: la urgencia se mide contra esta fecha">
          {corte ? <>Corte <b>{fechaPA(corte)}</b> · {horaPA(corte).split(", ").pop()} PTY</> : "…"}
          {meta?.agent_mode && meta.agent_mode !== "live" && <span className="modo">modo {meta.agent_mode}</span>}
        </div>
      </header>

      {error && <div className="aviso-global" role="alert">{error}</div>}

      <main className="contenido">
        {vista === "agenda" && <Agenda corte={corte} ficha={ruta.ficha} seccion={ruta.seccion} irAFicha={irAFicha} />}
        {vista === "consulta" && <Consulta inicial={ruta.q} irAFicha={irAFicha} />}
        {vista === "datos" && <Datos meta={meta} />}
        {vista === "evaluacion" && <Evaluacion irAFicha={irAFicha} />}
      </main>

      <footer className="pie">
        Prototipo hackIAthon 2026 · Datos públicos (TVN RSS solo metadatos, GDELT, Banco Mundial, USGS) ·
        Las salidas son borradores para revisión humana: <b>nada se publica automáticamente</b>.
      </footer>
    </div>
  );
}
