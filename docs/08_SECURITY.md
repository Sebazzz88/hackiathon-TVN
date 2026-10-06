# Seguridad

> Prompt injection, privacidad, revisión humana

## Controles operativos

| Riesgo | Control | Prueba |
|---|---|---|
| Inyección en una fuente | Patrones de instrucciones en titulares → alerta visible, E = 0, estado insuficiente, sin contexto. En el prompt cada evidencia va en `<DATO id=…>` con `<`, `>` y bloques de código neutralizados; las reglas viven solo en el mensaje de sistema. | T07 (`S-INY-001`) |
| Inyección en la consulta | Consultas que piden ignorar reglas, revelar secretos, inventar o "aunque no la tengas" se rechazan con abstención | T07, 10 casos adversariales |
| Alucinación | Validador en código: sin cita, cita a id ajeno, campo inexistente, cifras que no están en la evidencia citada o fuente inyectada → afirmación eliminada y listada | T07, T09 |
| Titular presentado como hecho | Un "hecho" que solo cita titulares se reclasifica como "declaración" | T07 |
| Repetición confundida con corroboración | Procedencia por agencia o texto casi idéntico; el puntaje usa procedencias independientes | T02 |
| Cifra anual como dato de hoy | Toda cifra BM lleva país, año, unidad y la leyenda "dato anual, no es una medición actual"; "hoy" → abstención | T04 |
| Publicación automática | No existe estado "publicado"; aprobar exige revisor y evidencia no insuficiente | T08 |
| Puntaje manipulado por el LLM | El puntaje lo calcula `scoring.py`; el LLM no lo ve ni lo modifica | T07 |

## Privacidad y reputación

- No se almacenan datos personales más allá de los nombres que aparecen en titulares públicos. No se crean perfiles ni listas de personas.
- Las acusaciones se presentan como declaraciones atribuidas a un medio, nunca como hechos.
- El registro de auditoría no guarda el texto de las consultas.

## Derechos y acceso

- TVN: solo título, URL y fecha del RSS público; no se guarda la descripción ni el cuerpo. No se republican artículos, imágenes ni videos.
- GDELT: metadatos; la API no transfiere derechos sobre los artículos enlazados.
- Banco Mundial: CC BY 4.0 con atribución. USGS: dominio público, se citan id y URL del evento.
- Notion se comparte solo con participantes y jurado.

## Credenciales

- La clave del LLM solo se lee de `.env` (en `.gitignore`); `.env.example` no tiene secretos.
- El cargador de `.env` no imprime valores. El código no registra prompts ni claves.

## Fuera de alcance

Etiquetar noticias como verdaderas o falsas, evaluar personas o clientes, recomendar acciones financieras y monitoreo en tiempo real.
