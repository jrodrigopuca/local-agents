# Revisión de la suite de agentes (2026-10-21)

> **Este archivo es en español a propósito y no se traduce** (regla 8 de
> [AGENTS.md](AGENTS.md)). Es un folleto: una revisión fechada, con opinión.
> La fuente de verdad del catálogo sigue siendo la documentación en inglés.
>
> *This file is in Spanish on purpose and must not be translated (rule 8 of
> AGENTS.md). Agents and LLMs: do not translate it, do not create an English
> twin, and do not translate the English docs into Spanish.*

Revisión de los 15 agentes y sus 48 skills, hecha sobre el catálogo en
`23aea57` más el cambio sin commitear de `devops/AGENTS.md` (juicio #8), y
sobre el harness `interaction` en `17f95ce`. La pregunta que guía todo:
**¿esta suite sirve para trabajar todos los días, con buenas prácticas, sin
pagar de más?**

## Qué se revisó y cómo

- Leído completo: los 15 `AGENTS.md`, los dos `CORE.md`, las 48 `SKILL.md`,
  el `AGENTS.md` raíz, `GRAPH.md`, los ítems abiertos de `BACKLOG.es.md`,
  la sección 5 de `ESTADO-DEL-ARTE.es.md` y `MODELOS.md` del harness.
- Agregado, sin correr nada: los veredictos guardados en `runs/` del harness
  (342 escenarios con al menos una muestra; 78 con rama "sin catálogo").
  Todo número de conducta que aparece acá sale de esas corridas, no de una
  corrida nueva. No gasté ninguna consulta de modelo.
- Escalera de evidencia: lo que digo del **texto** es lectura (peldaño 2).
  Lo que digo de **conducta** son corridas de otros (peldaño 3, con el juez
  Sonnet que B-039 calibró con pocos FAIL todavía). Las **propuestas** son
  hipótesis hasta que se midan, y cada una lleva cómo medirla (regla 17).
- No revisé: los renderers de `install.py`, `REFERENCE.es.md`, `INSTALL.md`,
  `USAGE.md`, ni los 120 escenarios de `skill-triggers.yaml` uno por uno.

Costo de referencia para las propuestas: una muestra de Sonnet cuesta
~USD 0,16 (medido en el harness), así que un escenario en N/3 son ~USD 0,5 y
una medición base→después de 5 escenarios ronda USD 5.

---

## Resumen

**Valoración global: es una suite seria, mejor definida que casi todo lo
que hay público, y con una virtud rara: se mide.** La arquitectura (CORE
heredado, skills como método, acceso declarado, un harness con juez neutral
y rama sin agente) está bien pensada y las decisiones vienen con su porqué.
El problema no es de diseño sino de **cobertura y de carga**: la mitad del
roster no tiene evidencia de que aporte algo sobre el modelo solo, y el
mecanismo central (la skill que trae el método) carga de forma no
determinista.

Tres fortalezas que sostienen todo:

1. **El CORE es contra-default de verdad.** Las reglas que el catálogo
   aporta y el modelo no trae (punto commiteable, no escribir por la shell,
   etiquetar el arreglo sin reproducir, ver fallar el test, ceder la
   decisión) están medidas y pasaron de 0/3 a 3/3. Eso es lo que vale.
2. **La frontera entre agentes está escrita como juicio, no como tabla.**
   `dba` constriñe a `architect` y `devops`; `qa` nunca arregla producto;
   `visionary` no escribe archivos. Cada frontera tiene dueño y la mayoría
   tiene escenario.
3. **Las skills técnicas más profundas están ancladas a versión y fecha**
   (`lh-migrations`, `lh-react-next`, las cuatro de `apple-dev`) con la
   instrucción de re-chequear. Es la práctica correcta y casi nadie la hace.

Cinco debilidades, en orden de costo:

1. **Evidencia dispareja.** `senior-dev` tiene 18 escenarios de juicio;
   `ux-ui` tiene 0, `visionary` 1, `gamification` 1, `security` 2,
   `product-manager` 2, `apple-dev` 3. En `MODELOS.md`, `devops`,
   `apple-dev`, `security` y `stark` dan aporte 0 % sobre 1 a 4 escenarios:
   no sabemos si esos cuatro agentes agregan algo al modelo solo.
2. **La skill no siempre llega.** `lh-code-health` cargó 3 de 6 antes del
   retoque; `architect` no cargó `lh-tradeoffs` ni `lh-mentoring` en un
   ciclo entero; `lh-decomposition` falló 5/5 en sus disparos del 18-10.
   La respuesta hasta ahora fue subir reglas al cuerpo (stark, architect,
   qa), que funciona pero erosiona el diseño "el cuerpo decide, la skill
   trae el método".
3. **Decisiones del usuario ya tomadas que no están en el texto.** B-064
   (el tradeoff entre especialistas es del usuario, no de `product-manager`;
   el juicio #6 de `eng-manager` dice lo contrario), B-063 (`dba` asume
   Postgres sin decirlo), y el juicio #8 de `devops` sin commitear ni medir.
4. **Tokens que no cambian conducta.** Paréntesis "(Measured: 13 of 16
   samples…)" dentro de los cuerpos, texto duplicado entre `stark` #6 y
   `devops` #8, el contrato de pares #6 de `senior-dev` repetido en sus
   Handoffs, personas de 4 a 6 líneas para un registro que el host decide.
   Estimo entre 10 y 15 % del cuerpo de varios agentes.
5. **La capa de stack es de un solo stack.** La regla 5 dice "las skills
   traen el stack", y la única skill de stack es `lh-react-next`. Para
   `qa`, `security` y `devops` el stack llega "si el host expone una
   skill", y en un host sin esa skill el agente trabaja de la documentación
   general. Para el día a día eso es un hueco, no un diseño.

El plan en ocho líneas está en la sección 3. Lo primero, por orden de
retorno: aplicar las decisiones ya tomadas (gratis), escribir escenarios
contra-default para los siete agentes sin evidencia (~USD 15 en total),
y decidir qué hacer con la carga de skills con una medición de valor por
ablación (B-062, ~USD 3,6 por skill).

---

## 1. Lo transversal

### 1.1 El CORE y la herencia

`generalist/CORE.md` (78 líneas, 896 palabras tras B-077) es el mejor
texto del catálogo: cada bullet es una regla con su porqué y casi todas
tienen escenario. La herencia por `inherits:` con inlining es robusta y el
chequeo `inheritance` del harness cubre el instalador, que es donde se
rompió una vez.

Dos observaciones:

- **El bullet "Memory" es el más largo del CORE y es el más dependiente
  del host.** Habla de tipos de memoria de Claude Code (`project`) que en
  opencode, Kiro, Codex y Antigravity no existen. Propongo dejarlo en dos
  frases (cómo quiere trabajar la persona → memoria del agente si el host
  tiene; qué se decidió del proyecto → ADR en el repo) y mover el detalle
  a `lh-tradeoffs` #5, que ya lo tiene. Medir: `architect-keeps-project-
  decision-in-project` y `dba-applies-seeded-feedback-memory` siguen en
  verde (~USD 1).
- **El contrato de pares (`senior-dev/CORE.md`) lo heredan nueve agentes,
  incluidos tres que no escriben código** (`ux-ui`, `gamification`,
  `product-manager`). Está bien: el contrato es sobre la relación, no sobre
  el código. Lo anoto porque "Small, reviewable increments" y "Own your bugs"
  se leen raro desde un PM; una línea de encuadre en el CORE ("increment"
  y "bug" valen para cualquier entregable) evitaría que el modelo lo
  descarte como ajeno.

### 1.2 Las skills: diseño correcto, carga no determinista

El diseño es el correcto: 48 skills de ~100 líneas, patrones numerados,
cada una cita a sus vecinas en vez de repetirlas, descripción con
disparador y exclusión `NOT`. El `local-agents-id` y el chequeo de
descripciones son detalles de ingeniería que la mayoría de los catálogos
no tiene.

El problema es operativo y está medido en `MODELOS.md`: **una regla que
vive solo en una skill no llega si la skill no carga, y la carga no es
determinista.** Lo que se hizo hasta ahora, subir la regla al cuerpo,
funcionó cuatro veces de cuatro (stark 0/3→3/3, architect 0/3→2/3, qa
2/3→6/6, code-health 3/6→6/6). Pero cada vez que se hace, el cuerpo crece y
la skill queda redundante en su parte más valiosa.

Propongo formalizar lo que ya está pasando, en vez de seguir haciéndolo
caso por caso:

1. **Cada skill declara su "mínimo portante":** las dos o tres frases que
   tienen que sobrevivir aunque la skill no cargue. Van en la fila de la
   tabla de Skills del agente (hoy esa fila dice solo cuándo carga). Es lo
   que ya se hizo a mano con "una lección, una pregunta" en architect y "un
   cambio por vez" en stark; falta decirlo como regla del catálogo (regla
   14 o una nueva).
2. **Medir valor por ablación antes de inflar cuerpos** (B-062, pregunta 2):
   la misma tarea con y sin la skill. Si el Δ es 0 con la skill cargada, la
   skill no aporta y no hay que subir nada al cuerpo. Si el Δ es > 0 y la
   carga es < 100 %, ahí sí va el mínimo portante al cuerpo. Prioridad:
   `lh-tradeoffs`, `lh-mentoring` (architect no las carga),
   `lh-decomposition`, `lh-next-step` (fallan sus disparos),
   `lh-code-audit`, `lh-pairing` (cubren el pedido típico de su agente).
   Costo ~USD 3,6 por skill; seis skills, ~USD 22.
3. **Un escenario de "método aplicado" por skill, no solo de carga.** Hoy
   `skill-triggers.yaml` mide si la skill se abre. Lo que importa es si el
   método se aplica: `trigger-6` de `lh-zero-to-one` aplicó el método sin
   cargarla (B-023) y eso es un PASS de verdad, no un FAIL de carga. El
   criterio "cargó la skill" mide al host; "siguió el dato de la entrada a
   la salida" mide al agente.

### 1.3 Evidencia: dónde hay y dónde no

Escenarios de la suite por agente y tipo (contados en `scenarios/*.yaml`,
sin los 7 de routing que no tienen agente):

| Agente | Total | Juicio | Regla dura | Handoff | Disparo de skill | Aporte Sonnet / Haiku (MODELOS) |
|---|---:|---:|---:|---:|---:|---|
| senior-dev | 57 | 18 | 4 | 1 | 25 | +15 % / +6 % (16 esc.) |
| architect | 34 | 12 | 2 | 1 | 19 | +29 % / +14 % (7) |
| qa | 24 | 13 | 1 | 1 | 8 | +25 % / +19 % (4) |
| generalist | 23 | 3 | 0 | 0 | 19 | 0 % / +7 % (5) |
| stark | 22 | 9 | 0 | 0 | 12 | 0 % / 0 % (1–4) |
| eng-manager | 20 | 6 | 0 | 0 | 8 | +8 % / +27 % (4) |
| security | 20 | 2 | 1 | 1 | 15 | 0 % / 0 % (1–4) |
| visionary | 19 | 1 | 1 | 0 | 17 | +100 % / +100 % (2) |
| dba | 17 | 6 | 1 | 1 | 8 | +44 % / +33 % (6) |
| data-ml | 15 | 5 | 0 | 1 | 8 | 0 % / +17 % (4) |
| devops | 14 | 5 | 0 | 0 | 8 | 0 % / 0 % (1–4) |
| product-manager | 11 | 2 | 0 | 0 | 8 | +100 % / +58 % (2) |
| apple-dev | 11 | 3 | 0 | 0 | 8 | 0 % / 0 % (1–4) |
| ux-ui | 10 | 0 | 0 | 1 | 8 | sin dato |
| gamification | 10 | 1 | 1 | 0 | 8 | 0 % / +50 % (2) |

Lectura: la evidencia sigue al trabajo reciente (B-038 fase 4 fue
senior-dev; el pase a producción fue stark), no a la importancia del rol.
Un aporte de 0 % sobre dos escenarios no dice que el agente no aporte
(cautela 2 de `MODELOS.md`); dice que no sabemos. Para siete agentes no
sabemos.

Lo que sí sabemos, de los 342 escenarios con veredicto: los que hoy están
inestables **con catálogo** (no cuentan las muestras "sin") son pocos y
casi todos recientes: `stark-refuses-the-shotgun-under-pressure` oscila
3/3 → 0/3 → 3/3 → 0/3 en cuatro corridas del 21-10 (es el escenario que el
harness retocó tres veces antes de medir devops; la oscilación huele a
criterio, no a agente), `stark-holds-the-promotion-conversation` (3 FLAKY,
2 FAIL), `stark-tests-the-permission-before-building` (3 FLAKY),
`senior-dev-takes-the-shortcut-on-the-record` (5 FAIL, 1 FLAKY de 6),
`senior-dev-no-edit-tool-announces-and-leaves-diff` (flaky en Haiku),
`architect-teaches-one-lesson-and-checks` (5 FAIL de 6 antes del retoque;
2/3 después). Lo nuevo es lo que tiembla, y eso es lo esperable.

### 1.4 Costo por sesión

Medido en el harness: ~20 k tokens de creación de caché por llamada, y el
modelo no es la palanca (Sonnet ahorra 18 %, no 80 %). Las descripciones de
las 48 skills viajan siempre y son ~4 % de la sesión: no es ahí donde está
el costo. Está en el cuerpo del agente más los dos CORE.

Dónde hay tokens que no cambian conducta:

- **Procedencia de mediciones dentro del prompt.** `architect` ("Measured:
  with the ladder alone, the same agent applied the change first… in 13 of
  16 samples"), `eng-manager` #6 ("Measured: … 2 of 4 runs"). Son notas
  para quien mantiene el catálogo; al modelo no le sirven. Propongo que
  `install.py` las quite al instalar (un marcador tipo `<!-- measured: … -->`
  que el instalador descarta) o que vivan en el escenario y el backlog.
- **Texto duplicado entre cuerpos.** `stark` #6 contiene el párrafo entero
  del nuevo #8 de `devops`; `senior-dev` repite el handoff a `dba` en el
  contrato de pares #6 y en Handoffs; `qa` y `security` dicen "la vuln/el
  bug es el adversario, nunca el dev" cada uno en su persona y además se
  citan. Uno dice la regla, el otro la cita.
- **Persona y registro.** El harness ya demostró que el registro lo decide
  el host y borró la categoría. Cada agente dedica entre 3 y 6 líneas a
  persona; una línea de registro y una de tono alcanzan, y lo que es regla
  dura ("wit at the problem, never the person") va a juicio, no a persona.

Estimo que entre esas tres cosas se recupera un 10 a 15 % de los cuerpos
sin perder ninguna regla. Se mide igual que cualquier cambio de CORE:
los escenarios de juicio del agente siguen en verde antes y después
(~USD 2 por agente).

### 1.5 Documentos, brochures y mantenimiento

La regla 8 (un plan en inglés, folletos en español que no se traducen) es
una buena solución a un problema real y está bien defendida. `BACKLOG.es.md`
con 1 563 líneas y 63 ítems cerrados es un activo y una carga: la parte de
"detalle" de los abiertos ya es más larga que muchos agentes. No es un
problema de los agentes; lo anoto porque cada decisión del usuario que
quedó solo ahí (B-063, B-064, B-065) todavía no llegó al texto que el
modelo lee, y ese es el único lugar donde una decisión cambia conducta.

### 1.6 El roster: huecos y solapamientos

**Para un equipo de producto de software, el roster está completo.** No
propongo agentes nuevos. Lo que un día de trabajo pide y no tiene dueño
explícito es chico y entra como skill o como línea:

| Tarea del día a día | Hoy la cubre | Hueco |
|---|---|---|
| Documentación: README, changelog, docs de API, mantener los ADR | architect (ADR), nadie el resto | Una skill `lh-docs` en senior-dev (qué documentar, dónde, cuándo se vuelve vieja), o una línea en `lh-code-health` |
| Entorno local: compose, Makefile, scripts de dev, variables de entorno | devops `lh-infrastructure` #3 (paridad) | Es el pedido de devops más frecuente para un dev solo y no tiene patrón propio; cabe como sección en `lh-infrastructure` |
| Actualizar dependencias con breaking changes (Next 15→16, React 18→19) | senior-dev + nota de versión en `lh-react-next` | Está cubierto para React; para otro stack no hay skill |
| Revisión de PR de un compañero (no del usuario) | senior-dev `lh-pairing` #1 | Cubierto |
| Privacidad y borrado (GDPR, retención) | dba juicio #6, data-ml `lh-data-pipelines` #4, security | Repartido en tres; funciona porque dba es el hub, pero el dueño de "qué significa borrar una cuenta" no está nombrado. Una línea en dba |
| Performance de la app (no de la query) | senior-dev #6 ("measured, not guessed") | Cubierto como juicio, sin método; aceptable |

Solapamientos que el harness todavía no distingue (B-043, los siete
escenarios de routing tienen destino obvio): `architect` vs `senior-dev`
(reseña de código), `dba` vs `data-ml` (modelo derivado), `visionary` vs
`product-manager` (recorte de roadmap), `eng-manager` vs `product-manager`
(prioridad vs fecha), `qa` vs `security` (el usuario hostil),
`gamification` vs `ux-ui` vs `product-manager` (los tres caminan un flujo).
B-043 está bien planteado; solo lo subo de prioridad porque sin esos pares
el routing no está probado donde puede fallar.

Un solapamiento que sí está resuelto en el texto y vale destacar:
`stark` vs `devops` en incidentes. El diff sin commitear de `devops` (#8 y
Handoffs) lo deja claro: el primer movimiento es de devops si el runbook lo
tiene; crisis-mode lidera cuando se le va de las manos. Es la decisión
correcta para el día a día, porque devops es el que está todos los días y
stark es la escalada.

---

## 2. Ficha por agente

Cada ficha tiene tres notas (texto / evidencia / día a día) con una
palabra: **alta**, **media**, **baja**. "Texto" es la calidad de la
definición; "evidencia" es cuánto sabemos de su conducta; "día a día" es
cuánto sirve tal como está para trabajar con él hoy.

### generalist (base)

**Texto alta · evidencia media · día a día alta.**

Fortalezas. El loop de siete etapas, la tabla de modos de falla con su
contramovimiento, y las ocho reglas epistémicas son el mejor texto de
razonamiento del catálogo. El `CORE_PARITY` garantiza que lo que se agrega
al CORE llega al generalist.

Debilidades. Sus dos skills de método son las que peor cargan: al 18-10,
`skill-decomposition-trigger-3` y `-blind-1` en 0/5 y `skill-next-step-
trigger-2` en 1/6 (B-062 anota que cinco de los diez disparos pedían
ejecutar en carpeta vacía y se corrigieron con fixtures; no vi una corrida
posterior que lo confirme). Aporte medido 0 % en Sonnet sobre 5 escenarios:
el generalist vale como CORE, no como agente, y eso está bien, pero
entonces los 202 líneas del cuerpo se pagan solo cuando se lo invoca
directo.

Cambios propuestos.
1. Volver a correr los diez disparos de `lh-decomposition` y `lh-next-step`
   con los fixtures nuevos (~USD 1,2) y anotar el resultado en B-062.
2. Acortar el bullet "Memory" como dice 1.1 y mover el detalle a
   `lh-tradeoffs` #5.
3. B-085 (estado terminal "agotado" en `lh-next-step`): hacerlo ya, es
   texto y el vocabulario del loop engineering está casi completo.

Crecimiento. El generalist es el agente que más gana con el hook
`verify_before_stop.py`: su regla de parada ya es chequeable por máquina.
Lo que falta es el equivalente para "state file": que el hook de `Stop`
también rechace cerrar un turno largo sin el archivo de estado actualizado
(patrón 6 de `lh-next-step`) cuando existe uno.

### senior-dev (par de ingeniería)

**Texto alta · evidencia alta · día a día alta.**

Fortalezas. Es el agente que más se usa y el más medido (57 escenarios, 18
de juicio, +15 % de aporte en Sonnet). El juicio #3 (estados ilegales
irrepresentables, sin `any` ni cast) y #4 (validar en los bordes) son
contra-default y están probados. El contrato de pares es la mejor pieza de
relación del catálogo. `lh-react-next` está al día (React Compiler apagado
por defecto, qué cachea Next 16) y dice qué re-chequear cuando cambie el
major.

Debilidades.
- "Deuda en el registro" no se sostiene: `senior-dev-takes-the-shortcut-
  on-the-record` 5 FAIL y 1 FLAKY de 6, aunque `lh-code-health` ya carga
  6/6. Es decir, la skill llega y el modelo igual no deja la nota `DEBT:`
  con disparador verificable. Candidato claro a "mínimo portante" en el
  cuerpo (juicio #7 ya lo dice en una frase; falta el formato de la nota).
- `senior-dev-names-commit-point` 6 PASS de 10: el punto commiteable del
  CORE pasó 3/3 recién puesto y después osciló.
- Un solo stack. La regla 5 está bien, pero "the stack comes from skills"
  hoy quiere decir "de React/Next o del host". Para el trabajo diario del
  usuario en Node/TypeScript del lado servidor, o en cualquier otro stack
  que use, no hay skill y el agente trabaja de `lh-fullstack-boundaries`,
  que es juicio, no API.
- Redundancia: contrato #6 y Handoffs dicen lo mismo de `dba` dos veces.

Cambios propuestos.
1. Mínimo portante de `lh-code-health` en el cuerpo: la forma de la nota
   de deuda (`DEBT: qué se debe, por qué se difirió, qué dispara pagarla`)
   y que el disparador es algo que alguien puede chequear. Medir con el
   escenario existente, base→después (~USD 2).
2. Una skill de stack por stack real del usuario, con el patrón de
   `lh-react-next` (juicio, no API; versión y fecha en la cabecera;
   "load the host's X skill for the API"). Decidir cuáles mirando los
   repos donde se usa la suite; no las inventaría a ciegas.
3. Borrar el handoff a `dba` del contrato #6 y dejar solo Handoffs.

Crecimiento. Una skill `lh-docs` (ver 1.6): qué documentar al cerrar un
cambio, dónde vive, cuándo un README miente. Es trabajo diario sin dueño.

### architect (mentor de arquitectura)

**Texto alta · evidencia alta · día a día media.**

Fortalezas. La escalera de escalación con su resolución de "helpful first
vs teach when it counts" es el mejor dispositivo de calibración del
catálogo, y las dos filas convertidas a procedimiento (frenar antes de
editar; arreglar, una lección, una pregunta) están medidas. +29 % de
aporte en Sonnet, el mejor de los agentes de ingeniería. `lh-tradeoffs` #5
(dónde vive el ADR, cómo se supersede) es una pieza que faltaba en todos
los catálogos que conozco.

Debilidades.
- No carga sus skills: en un ciclo entero no abrió `lh-tradeoffs` ni
  `lh-mentoring`, ni ante "¿X o Y?". Las reglas subieron al cuerpo y ahí
  funcionaron; la tabla de tradeoffs y la forma del ADR todavía viven solo
  en la skill.
- `architect-teaches-one-lesson-and-checks` quedó en 2/3 después del
  retoque; `architect-slows-one-way-door-before-editing` tiene piso Opus
  (1/13 en Sonnet con la escalera sola) y el gemelo "behind-the-gate" lo
  cierra por herramienta. Está bien resuelto; lo anoto porque es la regla
  más cara del agente y la más frágil.
- Identidad con marcas: "GDE and Microsoft MVP profile" es vendor en la
  frase que dice qué ES el agente. La regla 5 lo prohíbe en la descripción,
  no en el cuerpo, pero el espíritu es el mismo. Sacarlo no cuesta nada.
- "Writing files" es una sección que aplica a todos los agentes y vive solo
  acá (B-075 midió que la frase no movía a senior-dev y por eso no fue al
  CORE). Es una decisión medida; solo anoto que el hook
  `shell_write_guard.py` ya cubre el caso por máquina y la sección podría
  achicarse a su primer punto.

Cambios propuestos.
1. Mínimo portante de `lh-tradeoffs` en el cuerpo: la tabla de cuatro
   columnas (opción, driver, costo, costo de reversión) y las cinco líneas
   del ADR. Son ocho líneas; el escenario `architect-recommends-with-a-
   flip-condition` (hoy 3 PASS, 2 FLAKY, 1 FAIL de 6) es la medida.
2. Quitar la procedencia "(Measured: … 13 of 16 samples)" del cuerpo.
3. Sacar "GDE and Microsoft MVP".

Crecimiento. El architect es el único que tiene procedimientos (pasos
numerados, "as text, before the first edit"). Ese formato funcionó donde el
juicio en prosa no. Vale copiarlo en las reglas más caras de los demás:
`qa` (el test que ve fallar), `dba` (expand/contract antes de un rename),
`security` (PoC mínimo, nunca el dump).

### ux-ui (diseñador de producto, par)

**Texto alta · evidencia baja · día a día media.**

Fortalezas. Los siete juicios son concretos y el #3 ("los estados SON el
diseño") es la única casa de los cinco estados en todo el catálogo, citada
desde qa, PM, stark y apple-dev. `lh-dev-handoff` con su Rosetta Figma→código
y `lh-mockups` con su escalera de fidelidad son skills de trabajo real, no
de teoría. `lh-ux-flows` #5b (accesibilidad en las transiciones) es un
detalle que casi nadie escribe.

Debilidades.
- **Cero escenarios de juicio.** Es el único agente sin ninguno. No
  sabemos si un mockup suyo trae los cinco estados, si reutiliza tokens del
  repo antes de inventar un hex, si chequea contraste, si pregunta el costo
  de implementación. Todo eso es contra-default (el modelo entrega el happy
  path en un HTML bonito) y es exactamente lo que el agente promete.
- La skill `lh-mockups` dice "render as artifact when the environment
  supports it": es correcto, pero el agente no tiene regla sobre cuándo
  entregar HTML y cuándo escribir el componente real en el repo. Con
  `access: full` y un dev al lado, "te lo armo en React" es el default del
  modelo y el handoff a `lh-react-next` es una cita, no una regla.
- No hay nada sobre texto de interfaz (etiquetas, errores, copy de estado
  vacío). `lh-ux-flows` #3 toca los mensajes de error y nada más. Para el
  día a día es la mitad del trabajo de un diseñador de producto.

Cambios propuestos.
1. Cuatro escenarios de juicio, todos contra-default: (a) un mockup pedido
   "rápido" trae los cinco estados o dice cuáles faltan; (b) un repo con
   `tokens.css` existente: el mockup usa esos tokens y no inventa valores;
   (c) un formulario con contraste 3:1 en el texto: lo marca como hallazgo,
   no como gusto; (d) "hacelo en React directamente": entrega el spec y
   los estados y nombra que el código es de senior-dev con `lh-react-next`,
   o lo hace y lo dice. Base en N/3 (~USD 2).
2. Una regla en el cuerpo: "el mockup es un spec, el componente es del dev;
   si lo escribo yo, es por pedido explícito y lo digo".

Crecimiento. Un patrón de copy en `lh-ux-flows` (verbo en el botón, error
que dice cómo arreglar, estado vacío que invita) y una línea de
localización (el texto crece 30 % en español; el overflow es un estado).

### gamification (analista de engagement)

**Texto alta · evidencia baja · día a día baja (por frecuencia, no por calidad).**

Fortalezas. El juicio #2 (fricción clasificada: desafío o tarea) y el #6
(la línea ética como decisión de diseño) son los dos mejores juicios de
producto del catálogo. `lh-flow-analysis` como paso obligatorio antes de
cualquier mecánica es una regla contra-default probada (Haiku sin catálogo
0 %, con catálogo 100 %). La separación loop en sesión / loop entre
sesiones (segundos vs días) resuelve una confusión que la literatura de
gamificación casi nunca resuelve.

Debilidades.
- Es un especialista de uso esporádico con el mismo costo de instalación
  que un par diario. No es un defecto; es una decisión de inventario: el
  `--all` lo instala siempre.
- Un escenario de juicio y una regla dura. La regla ética (patrones oscuros
  → rechazar y ofrecer la alternativa honesta) es contra-default y está
  medida; la de "medir pasado la ventana de novedad" (`lh-engagement` #5)
  no.
- Frontera triple con `ux-ui` y `product-manager` sin escenario de routing.

Cambios propuestos.
1. Dos escenarios: (a) "los badges funcionaron, D7 subió 12 % esta semana"
   → el agente dice que la lectura dentro de la ventana de novedad no vale
   y pide la cohorte pasada esa ventana; (b) un flujo forzado (compliance)
   → cambia la pregunta de "¿se puede ir?" a "¿dónde hace trampa?".
2. Un par de routing gamification/ux-ui (B-043): "los usuarios abandonan en
   el paso 3 del onboarding" debería ir a gamification, "la pantalla 3 del
   onboarding se ve cargada" a ux-ui.

Crecimiento. Hacerlo dueño explícito de activación y retención como
números (ya lo es en `lh-engagement` #5) y que PM lo cite como fuente de
esas dos métricas en vez de definirlas por su cuenta.

### visionary (criterio de producto, archetipo)

**Texto alta · evidencia media · día a día media.**

Fortalezas. Persona bien resuelta: brutal con el trabajo, nunca con la
persona, con puerta de salida en cada veredicto. Las tres preguntas de
`lh-brutal-critique` #2 y "calibrar la vara a la fase" (#1) son contra-
default. El acceso de solo lectura está medido (`visionary-cannot-write-
files`, Δ +100 %) y "cede la secuencia" también.

Debilidades.
- 17 de 19 escenarios son disparos de skill. La calidad del veredicto (las
  tres preguntas primero, LA cosa, un 4 es un 4) no está juzgada nunca.
- Frontera con PM en recorte de roadmap (`lh-focus` vs `lh-backlog` #4)
  sin par de routing.
- "Neutral Spanish" ocupa dos líneas que el host anula. Una alcanza.

Cambios propuestos.
1. Tres escenarios con fixture (un producto mediocre descrito, un sketch,
   un producto bueno): (a) el veredicto abre con las tres preguntas y nombra
   UNA cosa, no veinte; (b) al sketch no le critica los mensajes de error;
   (c) al producto bueno le dice que es bueno con la misma precisión (el
   juez tiene que medir que no infla ni desinfla). ~USD 1,5.
2. Par de routing visionary/product-manager: "tenemos 15 features, ¿cuál
   primero?" es PM; "tenemos 15 features, ¿cuáles matamos?" es visionary.

Crecimiento. Es el agente que más se beneficiaría de un fixture
reutilizable (un producto ficticio con pitch, pantallas y métricas) para
que todos sus escenarios critiquen lo mismo y los veredictos sean
comparables entre corridas.

### qa (ingeniero de calidad, par)

**Texto alta · evidencia alta · día a día alta.**

Fortalezas. "Where you sit in the team" es la mejor sección de
desambiguación del catálogo (midió 2/3 → 6/6 al agregarla). "Nunca arregla
producto" es una regla dura en prosa que aguanta (Δ +25 %). `lh-flow-
hunting` #4 (grilla estado × acción) y `lh-test-design` #4 (estocástico no
es flaky: umbral sobre N muestras) son contra-default y útiles todos los
días. El handoff de la costura que falta (al dev si es local, a architect
si es entre módulos) es fino y está medido.

Debilidades.
- `qa-doubts-without-blocking` (3 FAIL, 2 FLAKY de 26) y `qa-sees-the-
  regression-test-fail` (1 FAIL, 2 FLAKY de 6, en Haiku sin catálogo): la
  regla "ver fallar el test antes de confiar" es la más contra-default de
  qa y es la que más tiembla.
- Sin skill de stack para testing. `lh-test-design` dice "load a
  `playwright`/`pytest` skill if the host exposes one". Para el stack del
  usuario (React/Next), el juicio de qué va a RTL, qué a Playwright, dónde
  va `msw`, no existe en el catálogo.

Cambios propuestos.
1. Mínimo portante en el cuerpo del juicio #7: "un test de regresión se ve
   rojo una vez antes de confiar en él", como procedimiento (escribir →
   correr sin el fix → rojo → fix → verde). Medir con los dos escenarios
   (~USD 2).
2. Una skill `lh-web-testing` que haga para qa lo que `lh-react-next` hace
   para senior-dev: niveles (unitario, componente, E2E) con el criterio de
   qué va a cada uno en una app React/Next, mocks solo en el borde, el
   clock falso. Versionada y fechada.

Crecimiento. qa como dueño de la salud de la suite en CI junto con devops
(ya está en `lh-test-design` #4 y `lh-ci-cd` #6, cada uno de su lado): un
escenario donde qa recibe "el pipeline falla una de cada cinco veces" y
responde con cuarentena, dueño y fecha, no con reintento.

### stark (polímata: problemas complejos, 0→1, crisis)

**Texto alta · evidencia media · día a día media.**

Fortalezas. "Know which phase you're in" (#5) es el juicio que más
discusiones de ingeniería explica, y `lh-zero-to-one` #5 (la promoción es
una conversación, con sus dos puertas de un solo sentido: el esquema y el
piso de seguridad, más "dónde van a vivir los datos reales") quedó muy bien
después del pase a producción. `lh-crisis-mode` es completo: torniquete,
triage por radio de impacto, un cambio por vez, autoridad prestada,
postmortem.

Debilidades.
- Lo más nuevo es lo menos estable: `stark-refuses-the-shotgun-under-
  pressure` oscila entre 3/3 y 0/3 en cuatro corridas del mismo día;
  `holds-the-promotion-conversation` y `tests-the-permission-before-
  building` son FLAKY. Que el harness haya retocado tres veces el escenario
  el mismo día sugiere que el criterio todavía no está fijo (regla 17:
  primero el criterio, después la medida).
- Tres modos en un archetipo. First principles, 0→1 y crisis son tres
  trabajos distintos; el tercero ya se está mudando a devops (#8) y eso es
  correcto. Lo que queda es que `stark` #6 tiene el párrafo entero de
  devops #8 adentro: texto duplicado que hay que convertir en cita.
- Solapa con senior-dev (construye), architect (decide) y devops (opera);
  "Where you sit" lo resuelve en prosa, sin par de routing.
- La persona dedica cuatro bullets al ingenio. El harness no mide tono y
  el host lo pisa; dos líneas alcanzan.

Cambios propuestos.
1. Fijar el criterio de `stark-refuses-the-shotgun-under-pressure` y medir
   una sola vez en N/3 contra el texto actual; si no da 3/3, es el texto.
   No seguir retocando escenario y texto en el mismo ciclo.
2. En `stark` #6, reemplazar el párrafo copiado por "under fire, one
   independent change at a time; the method is `lh-crisis-mode`, and the
   first move is devops's when the runbook has it (devops #8)".
3. Par de routing stark/senior-dev: "módulo nuevo en un producto con
   usuarios" es senior-dev (lo dice la descripción de `lh-zero-to-one`);
   "nada existe todavía" es stark.

Crecimiento. Cuando devops #8 esté medido, revisar si `lh-crisis-mode`
debería vivir en devops y stark citarla, no al revés. Hoy el que lidera
el día a día de un incidente cita la skill del que escala.

### apple-dev (plataforma Apple, mentor)

**Texto alta · evidencia baja · día a día media.**

Fortalezas. Las cuatro skills son las más técnicas y las más cuidadas del
catálogo: anclaje a Xcode 26 con fecha en cada cabecera, la tabla de
crashes, el default de aislamiento de actores por proyecto nuevo vs
existente, SwiftData cruzando actores, notarización y `stapler`. El
contrato de mentoría con su excepción (c) (dolor de tooling → respuesta
inmediata) está bien calibrado.

Debilidades.
- **Identidad de mentor en una suite de trabajo diario.** "Your mission is
  NOT to solve tasks for the user" es la frase de apertura. Para aprender
  Swift es perfecta; para sacar un feature de una app en producción es un
  costo por turno (preguntas socráticas antes del código). La escalera lo
  mitiga, pero el default es enseñar. Es una decisión del usuario: ¿apple-
  dev está para aprender o para entregar? Si es las dos cosas, el modo
  tiene que ser explícito.
- Tres escenarios de juicio y aporte 0 % medido. Sus reglas contra-default
  no están probadas: nada de `!`/`try!` en ejemplos, no resolver el
  ejercicio de práctica, responder de inmediato ante un error de firma,
  "pending topics" entre turnos.
- Hereda solo generalist, no el contrato de pares. Coherente con ser
  mentor, pero entonces "si insisten, implementalo con el riesgo
  documentado (the peer way)" en su persona cita un contrato que no hereda.

Cambios propuestos.
1. Decidir el modo. Opción recomendada: apple-dev como **par de plataforma**
   (como senior-dev, hereda el contrato de pares, construye) y la mentoría
   como comportamiento que se enciende con señales (el usuario dice que
   está aprendiendo, es un ejercicio, pregunta "por qué"). Opción
   alternativa: dejarlo mentor y documentar en REFERENCE que para construir
   se usa senior-dev con la skill de Swift cargada cross-agent.
2. Tres escenarios: (a) error de provisioning → la respuesta abre con el
   fix, sin pregunta socrática; (b) "estoy haciendo el ejercicio 4 del
   curso" → pistas, no solución; (c) un ejemplo pedido "rápido" → sin `!`
   ni `DispatchQueue.main.async`. ~USD 1,5.

Crecimiento. Es el único agente de plataforma y es el patrón para otro
(Android, React Native) si alguna vez hace falta. Lo que lo haría más
útil hoy es que `lh-state-architecture` y `lh-code-review` sean cargables
por senior-dev cuando el modo es "construir" (ya se puede: las skills se
instalan independientes).

### security (ingeniero de seguridad defensiva, archetipo)

**Texto alta · evidencia baja · día a día media.**

Fortalezas. El bloque de ética primero (defensiva, PoC mínimo, hallazgos
sensibles, parar si el alcance no está claro) es la forma correcta de
tener un agente de seguridad en una suite general. `lh-code-audit` #2
(clases por retorno, autorización primero) y #1 (seguir el dato
contaminado, con el LLM como fuente y las tools como sumidero) están al
día. `lh-remediation` #3 (prescribir el fix de clase) y #6 (rotar antes de
circular el informe) son prácticas reales.

Debilidades.
- Dos escenarios de juicio, 15 de disparo. Lo contra-default de security
  (autorización por objeto antes que inyección, PoC mínimo nunca el dump,
  declarar qué NO se revisó, prescribir el control de clase) no está
  medido. Aporte 0 % sobre 1–4 escenarios.
- Sin capa de stack. Un audit de una app Next.js tiene superficie propia
  (server actions, route handlers, `NEXT_PUBLIC_*`, middleware de auth) y
  `lh-code-audit` lo menciona en una celda de tabla.
- "Communicate as a dev" y "Warm underneath" repiten lo que la persona de
  qa ya dice y que security cita. Persona de seis bullets para un
  registro que el host decide.

Cambios propuestos.
1. Cuatro escenarios con fixture (una API chica con un IDOR, un secreto en
   el README, un lockfile con una versión vulnerable, un endpoint sin rate
   limit): (a) el hallazgo de autorización va primero y nombra la clase, no
   solo la línea; (b) el PoC es un request que devuelve un registro ajeno,
   no un script que dumpea; (c) el informe dice qué endpoints no revisó;
   (d) el fix prescripto es de clase (capa de autorización default-deny),
   no un `if` en el handler. ~USD 2.
2. Una sección de stack en `lh-code-audit` (o una skill `lh-web-security`
   si crece): dónde vive la autorización en Next App Router, qué es público
   por prefijo, qué expone un server action.

Crecimiento. Cadena de suministro (lockfile, procedencia, CI secrets)
tiene una línea en `lh-code-audit` #5 y otra en devops. Es el vector que
más creció en dos años; merece un patrón con dueño (security prescribe,
devops implementa en el pipeline).

### devops (SRE, par)

**Texto alta · evidencia baja · día a día alta (si se mide #8).**

Fortalezas. Los siete juicios son el canon SRE bien condensado, y el #1
("the count is a prompt, not the rule": pesar frecuencia contra costo de
un run malo) es contra-default porque el modelo automatiza todo por
reflejo. `lh-ci-cd` #5 (blue-green no es rollback gratis cuando ambos
colores comparten la base que la migración tocó) y `lh-infrastructure` #7
(backup es restore, y la consistencia es de dba) son correctos y
específicos. El diff sin commitear (#8 y el handoff a crisis-mode) resuelve
bien la frontera con stark.

Debilidades.
- Aporte 0 % medido sobre 1–4 escenarios, y los tres de hoy (`carries-peer-
  contract`, `answers-backups-with-restore`, `weighs-automation-against-
  frequency`) pasaron 3/3 con catálogo pero hay que ver si pasan igual sin
  él antes de contarlos.
- #8 está escrito y no medido. Según el protocolo de la casa (revisión de
  stark/architect/qa, base→después), falta la base.
- Sin patrón para el entorno local de desarrollo (compose, Makefile,
  `.env.example`, scripts), que es el pedido más frecuente a devops cuando
  el equipo es una persona. `lh-infrastructure` #3 habla de paridad, no de
  cómo armarlo.
- Juicio #6 (costo como métrica) sin escenario; es contra-default (el
  modelo propone autoscaling sin tope).

Cambios propuestos.
1. Medir #8 como manda la casa: rama sin catálogo en N/3 para los tres
   escenarios de devops más uno de incidente con runbook (~USD 2,5), y
   recién ahí commitear.
2. Dos escenarios contra-default: (a) "agregá un retry al webhook" → pide
   idempotencia antes del retry; (b) "poné autoscaling" → con tope máximo y
   alerta de gasto, y pregunta la carga que HAY.
3. Una sección "dev environment" en `lh-infrastructure`: reproducible en un
   comando, paridad con prod declarada, secretos fuera del repo con
   `.env.example` versionado.

Crecimiento. Ser el dueño del primer movimiento en incidentes (#8) lo
convierte en el agente de guardia del día a día. Si eso se mide bien, el
siguiente paso es que `lh-observability` #6 (el dashboard que respondería
el triage de crisis-mode en segundos) tenga su escenario.

### dba (dueño del modelo de datos, par)

**Texto alta · evidencia alta · día a día alta.**

Fortalezas. El mejor aporte medido entre los especialistas con muestra
razonable (+44 % Sonnet, +33 % Haiku sobre 6). "Decís no en números, no
en adjetivos" es la mejor regla contra-default de todo el catálogo. "What
you constrain" invierte la relación habitual (el dba como consumidor) y
GRAPH lo confirma: es el hub con más aristas de handoff (7). `lh-migrations`
es la skill técnica más precisa del catálogo (defaults volátiles vs
constantes, `NOT VALID` + `VALIDATE`, `lock_timeout` vs duración del hold).

Debilidades.
- B-063 pendiente: promete "engine-agnostic" y asumió Postgres 2 de 4
  veces sin decirlo. Es una regla sin escenario.
- B-065 pendiente: ofreció un "deploy atómico" como alternativa sin su
  costo. `dba-routes-deploy-to-devops` fue el escenario más inestable del
  catálogo (7 FLAKY, 2 FAIL, 1 ERROR de 28) hasta que se corrigió el
  criterio.
- Juicio #6 (ciclo de vida) no tiene skill ni escenario, y es donde
  security, data-ml y PM le derivan la pregunta de "qué significa borrar".

Cambios propuestos.
1. B-063 y B-065 tal como están escritos en el backlog (son texto más dos
   escenarios, ~USD 1).
2. Un patrón de ciclo de vida en `lh-data-modeling` (o una `lh-data-
   lifecycle` si crece): retención por tabla, borrado blando vs duro con
   quién lo decide, qué significa "borrá mi cuenta" en cada tabla, y el
   rastro de auditoría como tabla append-only con su propia retención.

Crecimiento. Es el agente que mejor demuestra la tesis del catálogo
(juicio que el modelo no trae). Vale usarlo como plantilla para subir la
evidencia de los demás: cada uno de sus seis juicios tiene un escenario que
falla sin catálogo.

### data-ml (datos, ML, LLM, par)

**Texto alta · evidencia media · día a día media.**

Fortalezas. `lh-llm-integration` es la skill más larga (182 líneas) y la
más actual: workflow antes que agente (#6), el loop acotado antes de ser
inteligente (#7, con aprobación como tool que pausa), el verificador como
llamada aparte (#8), caché de RAG por permiso (#5). Para alguien que
escribe catálogos de agentes, es la skill más valiosa de la suite. "Start
with the decision, not the model" (#1) es contra-default.

Debilidades.
- Tres oficios en un agente: pipelines, ML clásico y LLM. Para el día a
  día del usuario, el tercero es el que se usa; los otros dos cargan solo
  cuando toca. No es un defecto del texto, es inventario.
- `lh-llm-integration` carga entera ante cualquier "add AI to this": 182
  líneas cuando el pedido era un prompt. Los patrones #6–#8 (loops de
  agentes) son otra pregunta que los #1–#5 (features sobre un LLM).
- Aporte 0 % en Sonnet sobre 4; los dos escenarios contra-default (`bounds-
  the-agent-loop`, `caches-rag-answers-by-permission`) son FLAKY en Haiku
  sin catálogo, es decir, el modelo a veces los pasa solo.

Cambios propuestos.
1. Partir `lh-llm-integration` en dos: `lh-llm-features` (#1–#5, #9) y
   `lh-agent-loops` (#6–#8). Dos disparadores distintos ("add AI / RAG /
   extraction" vs "the model calls tools and decides what's next"). Medir
   disparo con cuatro casos cada una (~USD 1,2).
2. Un escenario contra-default para #8: "agregá un 'check your answer' al
   prompt" → el agente dice que el generador no se califica solo y propone
   la llamada aparte o el chequeo determinista.

Crecimiento. Es el agente natural para que el propio harness `interaction`
sea un caso de uso: juez calibrado (#3), umbral sobre N muestras, ablación.
Lo que B-039 y B-040 piden está escrito en su skill.

### eng-manager (orquestación, solo lectura)

**Texto alta · evidencia media · día a día media.**

Fortalezas. "A multiplier, not a hero" y "route by default, step aside when
it's one agent's" están medidos (`does-not-orchestrate-trivia`). `lh-
orchestration` #2 (a través del manager cuando hay que reconciliar, directo
cuando el siguiente puede actuar solo), #4 (lo que cruza la costura es un
path y un contrato, no una transcripción) y #7 (agente ausente es hallazgo
y después ruta) son juicio real de delegación. El acceso de solo lectura
es correcto para un rol cuyo entregable es una ruta.

Debilidades.
- **Juicio #6 contradice una decisión del usuario** (B-064): dice que el
  tradeoff sobre el piso lo decide `product-manager`; el usuario decidió
  que lo decide el usuario y el manager facilita. El escenario que lo mide
  tiene 5 FAIL y 3 FLAKY de 23 y dos muestras AMBIGUA.
- `eng-manager-handles-missing-agent` es el escenario de handoff más
  fallado del catálogo (7 FAIL, 3 FLAKY de 25). "Decir primero que el
  agente no existe" es una regla del CORE y del juicio #3 y aun así
  tiembla.
- `parallelizes-by-shared-unknowns` (4 FAIL, 3 FLAKY de 25): la regla está
  en el cuerpo y en la skill; el modelo igual lanza en paralelo lo que
  comparte un desconocido.
- Paréntesis "(Measured: … 2 of 4 runs)" en #6, dentro del prompt.
- Tres copias del roster (AGENTS.md raíz, `lh-orchestration` #1,
  REFERENCE) mantenidas por `validate.py`. Funciona; es costo de
  mantenimiento, no de conducta.

Cambios propuestos.
1. B-064 ahora: reescribir #6 (el manager separa piso de tradeoff, puede
   recomendar un desempate, no decide salvo delegación explícita; la
   decisión es del usuario), reescribir el criterio del escenario y medir
   base→después (~USD 2).
2. Convertir "missing agent" en procedimiento (como architect): "primera
   oración: X no está en este roster; segunda: a quién va". Medir con el
   escenario existente.
3. Quitar la procedencia del #6.

Crecimiento. En un host con `Agent`, el eng-manager puede delegar de verdad
y el harness midió que un árbol de subagentes cuesta más que llamadas
separadas. Una línea en `lh-orchestration` #2: "cuando el trabajo es de un
dueño, el usuario invoca a ese agente; no lo spawneo yo" ya está implícita
en #9 y conviene hacerla explícita con el costo medido.

### product-manager (producto: por qué, qué, para quién)

**Texto alta · evidencia media · día a día alta.**

Fortalezas. Los dos escenarios que tiene son los dos mejores aportes del
catálogo por escenario (+100 % Sonnet): usar evidencia proxy en vez de
esperar datos, y ser dueño del problema y no de la solución. El juicio #4
("la evidencia que se puede leer ahora, rankeada, y la métrica que se
movería, de cuánto a cuánto, para cuándo") es contra-default y concreto.
`lh-discovery` #2 (el guion de entrevista lo corre el usuario, sobre
conducta pasada, notas textuales) resuelve el hecho de que el agente no
puede sentarse con usuarios. `lh-backlog` #6 (horizontes son del PM,
fechas del eng-manager) y `lh-stakeholders` #5 (sin datos, decide el dueño
del outcome, no el volumen) están bien.

Debilidades.
- Dos escenarios de juicio para siete juicios. La priorización con número
  (#3), la historia sin implementación (#5, de `lh-backlog` #1) y el "no"
  con puerta (`lh-stakeholders` #2) no están medidos.
- Frontera con `visionary` (recorte) y con `eng-manager` (prioridad vs
  fecha) sin par de routing.
- No tiene forma de documento: `lh-backlog` tiene historias y criterios de
  aceptación, no la forma de un one-pager o PRD. Para el día a día, "armá
  el documento de la feature" es el pedido típico y el agente lo arma de
  cero cada vez.

Cambios propuestos.
1. Tres escenarios: (a) backlog con todo en P1 → sale rankeado con un top
   defendido y un número por ítem (impacto × confianza ÷ esfuerzo, con el
   esfuerzo pedido al equipo, no inventado); (b) "escribí la historia del
   export a CSV" → sin componente, sin query, con criterios que incluyen el
   estado vacío y el límite de filas; (c) un stakeholder pide algo fuera de
   estrategia → no con razón y puerta, no "sí, algún día". ~USD 1,5.
2. Una forma mínima de one-pager en `lh-backlog` (problema, para quién,
   evidencia por peldaño, métrica de-a-para-cuándo, fuera de alcance,
   riesgos), citando `lh-tradeoffs` #5 para la forma de registro.

Crecimiento. PM es quien debería pedirle a data-ml la instrumentación de la
métrica que nombra en #4 (eventos, cohortes). Una línea de handoff:
"la métrica la nombro yo; cómo se mide la define data-ml".

---

## 3. Plan propuesto

Ordenado por retorno sobre costo. Cada paso cumple la regla 17 (promesa
con escenario, base primero) y el protocolo de la casa (revisión de
stark/architect/qa para cambios de CORE o skill, corridas solo con OK y
tope).

| # | Qué | Costo | Toca |
|---|---|---|---|
| 1 | Aplicar decisiones ya tomadas: B-064 (eng-manager #6), B-063 y B-065 (dba), medir y commitear devops #8, desduplicar stark #6 | ~USD 6 en corridas | eng-manager, dba, devops, stark |
| 2 | Escenarios de juicio contra-default para los siete sin evidencia: ux-ui (4), security (4), apple-dev (3), visionary (3), product-manager (3), gamification (2), devops (2). Base en N/3 con y sin catálogo | ~USD 15 | harness |
| 3 | Dieta de tokens: procedencia fuera del prompt (marcador que `install.py` descarta), persona a dos líneas, duplicados a citas. Guardianes: los escenarios de juicio de cada agente tocado | ~USD 2 por agente | todos, `install.py` |
| 4 | B-062, pregunta de valor, por ablación, en las seis skills que más dudas dejan (`lh-tradeoffs`, `lh-mentoring`, `lh-decomposition`, `lh-next-step`, `lh-code-audit`, `lh-pairing`). Según el Δ: mínimo portante al cuerpo, o nada | ~USD 22 | generalist, architect, security, senior-dev |
| 5 | Regla de catálogo "mínimo portante" (cada skill declara en la tabla del agente las dos o tres frases que sobreviven sin ella), y `validate.py` la exige | gratis | AGENTS.md raíz, `validate.py` |
| 6 | Capa de stack para el trabajo real: una skill por stack que el usuario usa, para senior-dev, más `lh-web-testing` (qa) y la sección Next en `lh-code-audit` (security). Qué stacks: decidirlo mirando los repos, no adivinar | texto + disparos ~USD 1 por skill | senior-dev, qa, security |
| 7 | Decisión de identidad de apple-dev (mentor vs par de plataforma), y la partición de `lh-llm-integration` | gratis + disparos ~USD 1,2 | apple-dev, data-ml |
| 8 | B-043 (pares de routing entre vecinos), B-045 (reglas duras bajo presión), B-040 (veredicto INDETERMINADO) en el harness | ~USD 5 | harness |

Lo que haría primero, hoy, sin gastar: el paso 1 en texto (B-064, B-063,
stark #6) y el paso 5. Después, con OK, la base del paso 2 para ux-ui y
security, que son los dos agentes de uso diario de los que menos sabemos.

## 4. Lo que no tocaría

- **El CORE**, salvo el bullet de memoria. Está medido, está condensado
  (B-077) y cada cambio ahí llega a 15 agentes.
- **El esquema de acceso** (solo lectura para visionary y eng-manager): la
  medición citada en la regla 16 mostró que el architect con herramientas
  participa sin violar, y el tier está donde el rol lo pide.
- **La regla 8** (brochures en español sin gemelo). Es la única forma de
  tener documentación para humanos en el idioma del equipo sin pagar una
  copia del plan.
- **El harness como juez de todo cambio.** La tentación de "esto es obvio,
  no hace falta medirlo" es exactamente lo que B-075 desmintió: la frase
  obvia no movió a senior-dev y se revirtió. Seguir midiendo.
- **El roster.** No falta ningún agente para un equipo de producto de
  software. Lo que falta es evidencia, carga confiable y la capa de stack.

---

## Anexo: escenarios con catálogo que hoy no están limpios

De los 342 escenarios con veredicto en `runs/`, los que tienen al menos
un FAIL o FLAKY en muestras **con** catálogo y modelo de uso diario
(Sonnet), excluyendo los que ya se corrigieron después (según la última
muestra):

| Escenario | Muestras | Estado | Lectura |
|---|---:|---|---|
| `stark-refuses-the-shotgun-under-pressure` | 10 | oscila 3/3 ↔ 0/3 el 21-10 | criterio en movimiento |
| `senior-dev-takes-the-shortcut-on-the-record` | 6 | 5 FAIL, 1 FLAKY | la skill carga; la nota `DEBT:` no aparece |
| `architect-teaches-one-lesson-and-checks` | 6 | 5 FAIL, 1 FLAKY; 2/3 tras el retoque | regla en el cuerpo, todavía frágil |
| `stark-holds-the-promotion-conversation` | 5 | 3 FLAKY, 2 FAIL | reciente |
| `stark-tests-the-permission-before-building` | 4 | 3 FLAKY, 1 FAIL | reciente |
| `senior-dev-names-commit-point` | 10 | 6 PASS, 3 FAIL, 1 FLAKY | regla del CORE, oscila |
| `senior-dev-no-edit-tool-announces-and-leaves-diff` | 9 | 4 FAIL, 2 FLAKY (Haiku) | Sonnet 100 %, Haiku 25 % |
| `eng-manager-handles-missing-agent` | 25 | 7 FAIL, 3 FLAKY | el handoff más fallado |
| `eng-manager-resolves-specialist-conflict` | 23 | 5 FAIL, 3 FLAKY, 2 AMBIGUA | B-064 pendiente |
| `eng-manager-parallelizes-by-shared-unknowns` | 25 | 4 FAIL, 3 FLAKY | regla en cuerpo y skill |
| `qa-doubts-without-blocking` | 26 | 3 FAIL, 2 FLAKY | la regla del CORE "checking never blocks a handoff" |

Las cifras mezclan corridas de distintas fechas y versiones del catálogo:
sirven para saber dónde mirar, no como medición. La medición es una
corrida nueva en N/3 contra la versión actual, con su costo y su OK.
