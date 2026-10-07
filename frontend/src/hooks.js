import { useEffect, useState } from "react";

/** Segundos transcurridos mientras `activo` es verdadero (vuelve a 0 cada vez que empieza). Para los botones que
 *  esperan a la IA local o a las pruebas: "Generando… 12 s". */
export function useSegundos(activo) {
  const [seg, setSeg] = useState(0);
  useEffect(() => {
    if (!activo) return;
    setSeg(0);
    const t = setInterval(() => setSeg((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, [activo]);
  return seg;
}
