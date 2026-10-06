# Riesgos y ética

| Riesgo | Tipo | Control operativo | Evidencia |
|---|---|---|---|
| Una fuente intenta cambiar las instrucciones | Ataque al agente | Detección por patrones → E = 0 y alerta; datos aislados en `<DATO>`; validador descarta lo que no tenga cita válida | T07, caso `S-INY-001` |
| El usuario pide inventar o revelar secretos | Ataque al agente | Rechazo con abstención | 10 consultas adversariales del benchmark |
| Cifras o citas inventadas | Anti-alucinación | Validador en código con control de cifras | T07, T09, prueba con cliente LLM simulado |
| Repetición tomada como corroboración | Sesgo | Procedencias independientes; agencia replicada = 1 | T02 |
| Dato anual presentado como actual | Exactitud | País, año, unidad y leyenda en cada cifra BM | T04 |
| Publicación sin revisión | Control humano | No existe estado "publicado"; aprobar exige revisor | T08 |
| Acusaciones contra personas | Reputación | Se presentan como declaraciones atribuidas, no como hechos | Reclasificación hecho → declaración |
| Datos personales | Privacidad | No se guardan más datos que los titulares públicos; el audit no guarda consultas | `backend/app/main.py` |
| Derechos de TVN y medios | Derechos | Solo título, URL y fecha; sin descripción, cuerpo, imágenes ni video | D02 |
| Fuga de la clave del LLM | Credenciales | Solo en `.env` (ignorado por git); nunca en prompts ni logs | Prueba con cliente simulado |
| Sesgo de idioma o región | Sesgo | Modelo multilingüe; vínculo con Panamá explícito en R | D05, D09 |
| Supuestos editoriales en el puntaje | Sesgo | Alcance sectorial por tema documentado como supuesto pendiente de validar con editor | `docs/04_AGENT.md` |

## Escenarios fuera de alcance

Detectar noticias falsas de forma definitiva, evaluar personas o clientes, recomendar decisiones financieras, publicar contenido, leer artículos detrás de paywall y monitoreo en tiempo real.
