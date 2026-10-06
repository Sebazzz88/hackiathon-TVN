import { useState } from "react";
import { ESTADOS, api, estadoTxt, horaPA } from "../lib.js";

export default function Revision({ f, onCambio }) {
  const [revisor, setRevisor] = useState(() => { try { return localStorage.getItem("revisor") || ""; } catch { return ""; } });
  const [comentario, setComentario] = useState("");
  const [error, setError] = useState("");
  const bloqueado = f.estado_evidencia === "insuficiente";

  const registrar = (estado) => {
    if (revisor.trim().length < 2) return setError("Escribe el nombre de la persona revisora.");
    try { localStorage.setItem("revisor", revisor); } catch { /* sin almacenamiento local */ }
    setError("");
    api(`/fichas/${f.id_caso}/review`, "POST", { estado, revisor, comentario })
      .then((x) => { onCambio(x); setComentario(""); })
      .catch((e) => setError(e.message));
  };

  return (
    <div className="panel">
      <p className="estado-actual">Estado actual: <b>{estadoTxt(f.estado_revision)}</b></p>
      <div className="campos">
        <label>Persona revisora
          <input value={revisor} onChange={(e) => setRevisor(e.target.value)} placeholder="Nombre y apellido" />
        </label>
        <label>Comentario
          <textarea rows={2} value={comentario} onChange={(e) => setComentario(e.target.value)}
            placeholder="Corrección, evidencia que falta o motivo de descarte" />
        </label>
      </div>
      <div className="estados">
        {ESTADOS.map(([k, t]) => {
          const off = k === "aprobado_como_borrador" && (bloqueado || !f.borrador);
          return (
            <button key={k} className={"estado" + (f.estado_revision === k ? " on" : "") + (k === "descartado" ? " peligro" : "")}
              onClick={() => registrar(k)} disabled={off}
              title={off ? (bloqueado ? "Evidencia insuficiente: requiere investigación" : "Genera el borrador antes de aprobar") : ""}>
              {t}
            </button>
          );
        })}
      </div>
      {error && <p className="error">{error}</p>}
      <p className="nota">
        Aprobar como borrador <b>no publica</b>. {bloqueado && "Este tema tiene evidencia insuficiente: no se puede aprobar. "}
        La decisión editorial final es de la persona revisora.
      </p>
      {f.revisiones?.length > 0 && (
        <>
          <h3 className="kicker">Historial</h3>
          <ol className="historial">
            {[...f.revisiones].reverse().map((r, i) => (
              <li key={i}><span className="meta">{horaPA(r.ts)}</span> <b>{r.revisor}</b> → {estadoTxt(r.estado)}{r.comentario && <q>{r.comentario}</q>}</li>
            ))}
          </ol>
        </>
      )}
    </div>
  );
}
