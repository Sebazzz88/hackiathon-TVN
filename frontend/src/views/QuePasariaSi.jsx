import { COMPONENTES } from "../lib.js";
import { PESOS_RETO, REGLAS, normalizar } from "../puntaje.js";

/** Controles de la vista "¿qué pasaría si…?": cambia los pesos y la lista muestra el ranking simulado. No guarda nada. */
export default function QuePasariaSi({ pesos, setPesos, cuantos }) {
  const norm = normalizar(pesos);
  const iguales = Object.keys(PESOS_RETO).every((k) => Number(pesos[k]) === PESOS_RETO[k]);
  return (
    <section className="que-pasaria" aria-label="Simulación de pesos">
      <div className="qp-cab">
        <p className="kicker">¿Qué pasaría si…? · simulación sin guardar</p>
        <button className="seg" onClick={() => setPesos({ ...PESOS_RETO })} disabled={iguales}>Pesos del reto ({REGLAS})</button>
      </div>
      <div className="qp-sliders">
        {COMPONENTES.map(([k, nombre]) => (
          <label key={k}>
            <span><b>{k}</b> {nombre}</span>
            <input type="range" min={0} max={60} step={1} value={pesos[k]}
              onChange={(e) => setPesos({ ...pesos, [k]: Number(e.target.value) })} aria-valuetext={`${Math.round(norm[k])} de 100`} />
            <span className="num">{Math.round(norm[k])}</span>
          </label>
        ))}
      </div>
      <p className="nota">
        Los pesos se normalizan para sumar 100. El ranking oficial sigue usando {REGLAS} (30/25/20/15/10); esto solo muestra
        cómo cambiaría el orden de los {cuantos} temas cargados (usa <b>Máx</b> para simular sobre todos).
        Para cambiar las reglas de verdad hay que registrar la decisión en docs/09_DECISIONS.md y subir la versión.
      </p>
    </section>
  );
}
