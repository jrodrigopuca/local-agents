# Estado del arte: agentes y skills

> **Este archivo es en español a propósito y no se traduce** (regla 8 de
> [AGENTS.md](AGENTS.md)). Es un folleto, no un segundo plano: la fuente de
> verdad es la documentación en inglés. Si sos un agente o un LLM: no lo
> traduzcas, no generes una versión en inglés, y no traduzcas los documentos en
> inglés a español. Si algo de acá queda desactualizado, corregilo en español.
>
> *This file is in Spanish on purpose and must not be translated (rule 8 of
> AGENTS.md). Agents and LLMs: do not translate it, do not create an English
> twin, and do not translate the English docs into Spanish.*

**Relevado el 2026-10-11; la comparación con otros catálogos y con las
prácticas de evaluación (sección 3), el 2026-10-12. Actualizado el 2026-11-10:
la donación de Agent Skills (sección 1), los subagentes en cada host (sección
2), lo que recomiendan los hosts sobre subagentes (sección 3) y los cambios de
Claude Code de octubre y noviembre (sección 4). Próxima revisión: 2027-01, o
antes si un host cambia de versión mayor o aparece un estándar nuevo.**

Qué está pasando en la industria con los agentes y las skills, dónde estamos
frente a otros catálogos, qué medimos nosotros contra los hosts reales, qué
consideraciones salen de eso para el catálogo, y el backlog que se desprende. Las recetas y los detalles de cada host
están en [INSTALL.md](INSTALL.md) y [USAGE.md](USAGE.md); acá solo va lo que no
se deduce de ellos.

Cada dato lleva su origen:

- **Medido**: lo probamos contra el host instalado, con versión.
- **Documentado**: lo dice la doc oficial del host, sin probar.
- **Reportado**: lo dice una fuente secundaria (blog, foro, nota).

La distinción importa: el 2026-10-11 la doc oficial de dos hosts resultó estar
mal, y solo una prueba lo mostró.

---

## 1. Lo que se estandarizó

### Skills: Agent Skills (`SKILL.md`)

- Anthropic lo publicó como estándar abierto en diciembre de 2025. La
  especificación vive en [agentskills.io](https://agentskills.io).
  *Reportado.*
- La [lista oficial de clientes](https://agentskills.io/clients) tenía unos 45 al
  2026-10-11, entre ellos Claude Code, Codex, OpenCode, Kiro, Gemini CLI,
  Cursor, GitHub Copilot y VS Code. *Documentado.*
- Antigravity no figura en esa lista, pero lee `SKILL.md`: vio las 48 skills del
  catálogo. *Medido, agy 1.3.3.*
- El catálogo valida cada skill contra la implementación de referencia
  (`skills-ref`) en CI.
- **Cambió de dueño (2026-10-22).** Anthropic [donó Agent Skills](https://www.anthropic.com/news/donating-agent-skills-to-the-agentic-ai-foundation)
  a la Agentic AI Foundation, la misma fundación de la Linux Foundation que
  ya tenía MCP y `AGENTS.md`: el estándar, el nombre, la organización de
  GitHub y el dominio. Lo mantienen ingenieros de Anthropic, Google, OpenAI y
  otros, a título personal. El anuncio habla de más de 70 plataformas que lo
  integraron, 1 millón de skills publicadas y cerca de 280 millones de
  instalaciones. *Documentado.*
- La hoja de ruta propuesta, todavía no definitiva, tiene tres cosas:
  **versiones publicadas**, un **proceso formal de propuestas** y una **guía
  de seguridad** para quien escribe e instala skills. Las dos que nos tocan:
  hoy fijamos `skills-ref` a un commit porque no hay versiones (regla 12), y
  la guía de seguridad va a opinar sobre lo que B-058 resolvió por su cuenta
  (de quién es una skill que comparte nombre con otra). B-096. *Documentado.*

### Instrucciones de repo: `AGENTS.md`

- OpenAI lo donó a la [Agentic AI Foundation](https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation)
  de la Linux Foundation en diciembre de 2025, junto con MCP. *Documentado.*
- Se reportan más de 60.000 repos que lo usan; el número es de fines de 2025.
  *Reportado.*
- Un [estudio en arXiv](https://arxiv.org/html/2601.20404v2) midió que con
  `AGENTS.md` los agentes terminan antes (de 163 s a 130 s de media) y gastan
  menos tokens. *Reportado.*

---

## 2. Lo que NO se estandarizó: los agentes

No hay un formato común para definir subagentes, y no parece que vaya a haberlo
pronto:

- Cada host tiene el suyo: markdown con frontmatter (Claude Code, opencode,
  Antigravity, cada uno con otros campos y otros nombres de herramientas), JSON
  (Kiro) o TOML (Codex). [Comparativa](https://www.morphllm.com/subagent).
  *Reportado; los formatos de Codex y Antigravity, medidos.*
- [Agent Plugins 1.0](https://blakecrosley.com/blog/agent-plugins-standard), el
  estándar de empaquetado publicado en agosto de 2026 por Vercel, OpenAI,
  Microsoft, GitHub, Cursor y Amazon (Google se sumó al lanzamiento), excluye a
  propósito agentes, hooks y reglas, por ser "too client-specific for a stable
  portable contract". Empaqueta skills y servidores MCP. Anthropic no participa
  y Claude Code mantiene su propio formato de plugins. *Reportado.*
  La [especificación 1.0.0](https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md)
  lo confirma (*documentado*): un plugin es una carpeta con `plugin.json`
  (obligatorios `$schema` y `name`), `skills/` en un solo nivel y un `mcp.json`
  opcional. No define registro, marketplace ni dónde se instala: el mínimo que
  exige a un cliente es cargar un plugin desde una ruta. Lo propio de cada
  cliente va bajo un namespace de dominio invertido. Codex lo soporta desde la
  0.146 (*reportado*).
- Al 2026-11-10 nada de eso cambió: Agent Plugins sigue en borrador y sigue
  empaquetando solo skills y servidores MCP. *Reportado.* Lo que sí se movió
  es cuánto difieren los hosts entre sí, ya no solo en el formato:

  | | Claude Code | Codex | VS Code (agente local) |
  |---|---|---|---|
  | Archivo | `.claude/agents/*.md` | TOML en `.codex/agents` | `.github/agents/*.agent.md` |
  | Un subagente puede lanzar otro | Sí, hasta 3 niveles por defecto (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`) | Solo un nivel por defecto (`agents.max_depth = 1`) | No por defecto; con un ajuste, hasta 5 |
  | Quién puede delegar en quién | Cualquiera con la herramienta `Agent` | Sin campo conocido | `agents:` lista los subagentes permitidos; `[]` lo prohíbe |
  | Modelo | Parámetro de la llamada, después `model:` del agente, después el de la conversación | Sin relevar | Igual orden, y un modelo más caro que el de la conversación no corre |

  Claude Code y VS Code, *documentado* ([sub-agents](https://code.claude.com/docs/en/sub-agents),
  [VS Code](https://code.visualstudio.com/docs/agents/run/subagents), página
  del 2026-11-04); Codex, *reportado* (el resumen de su doc, no la página).
  VS Code no es un host al que instalemos; va como referencia.
- El frontmatter de un agente de Claude Code creció bastante más allá de lo
  que `install.py` escribe (`name`, `description`, `tools`, `model`,
  `memory`): hoy también acepta `effort`, `maxTurns`, `permissionMode`,
  `disallowedTools`, `isolation: worktree`, `omitClaudeMd`, `hooks`,
  `mcpServers` y **`skills:`**, que inyecta el contenido entero de las skills
  listadas al arrancar el agente (hasta 32). Un campo que no reconoce se
  ignora sin avisar. *Documentado.* `skills:` importa acá más que el resto:
  es una respuesta del host a nuestro problema medido de que la skill no
  siempre carga (B-062), al precio de pagarla en cada turno. B-093.
- Los catálogos que apuntan a varios hosts, como
  [wshobson/agents](https://github.com/wshobson/agents), mantienen una sola
  fuente y generan la instalación para cada host. *Documentado* (detalle en la
  sección 3).
- Evaluar agentes en tareas largas y con varios agentes sigue sin solución
  estándar; las herramientas actuales cubren bien tareas de un turno y llamadas
  a herramientas ([O'Reilly](https://www.oreilly.com/radar/the-ai-agents-stack-2026-edition/)).
  *Reportado.*

---

## 3. Dónde estamos frente a otros catálogos (2026-10-12)

Leímos el repo y la documentación de cada proyecto; **no instalamos ni corrimos
ninguno**. Salvo que se indique otra cosa, los datos son *documentados* (los
dice la doc del propio proyecto), y las estrellas y los conteos son
*reportados* (los mostraba GitHub ese día). Que un proyecto tenga muchas
estrellas no dice nada de su rigor: el caso más popular de esta lista
reconoce en su propia doc que su juez LLM no está validado.

### El caso más cercano: wshobson/agents

[wshobson/agents](https://github.com/wshobson/agents) (unas 40.500 estrellas)
es el que más se parece a este catálogo en arquitectura y el que más se aleja
en filosofía.

| | wshobson/agents | este catálogo |
|---|---|---|
| Tamaño | 94 plugins, 202 agentes, 184 skills, 105 comandos | 15 agentes, 48 skills |
| Qué define a un agente | El stack (`python-pro`, agentes de Django, de Kubernetes…) | El criterio; el stack lo traen las skills (regla 5) |
| Fuente única y generación por host | Sí: adaptadores para Codex, Cursor, OpenCode, Copilot, Antigravity y Pi sobre una matriz común (`capabilities.py`); lo generado no se versiona | Sí: `install.py` para 5 hosts, con sello de procedencia (`--status`, `--refresh`) |
| Distribución | Marketplace de plugins de Claude Code; se instala por plugin | Copia por host o por proyecto; sin marketplace (B-028, en espera) |
| Topes de tamaño | Archivos de contexto de ~150 líneas; cuerpo de skill de ~8 KB, el límite que le atribuyen a Codex; lo que sobra se parte en `references/` | Ninguno, y en Codex no hace falta: recibe entera la copia instalada de `lh-llm-integration`, de 10.907 bytes (*medido*, 0.162.1, B-042) |
| Modelo por agente | `model:` en cada agente: 70 sonnet, 54 opus, 52 inherit, 24 haiku, 2 fable | `inherit`; en B-036, el único caso donde Sonnet fallaba y Opus no se resolvió reescribiendo la regla, sin cambiar de modelo |
| Acceso | `tools:` por agente | `access: read\|full`, traducido a lo que cada host hace cumplir (regla 16) |
| Orquestación | Cadenas fijas en slash commands (p. ej. backend → base de datos → frontend → tests → seguridad → deploy → observabilidad) | `eng-manager` rutea según dónde está el peso del trabajo; delegar costó ~4× (medido una vez: USD 3,06 contra 0,69) |
| Validación estática | `make validate` y `make garden` (detector de deriva: links muertos, skills demasiado grandes, plugins huérfanos), cada hallazgo con su remedio | `validate.py` con 25 chequeos y `skills-ref` fijado a un commit, en CI |
| Humo en hosts reales | En CI instala los CLI de OpenCode, Antigravity y Pi | `smoke.py` para 5 hosts, local: consulta al modelo y necesita credenciales |
| Evaluación de comportamiento | PluginEval: solo la capa 1 (lint estático) es confiable. Según su doc, el juez LLM hace una llamada por dimensión, sin repeticiones, y "no está validado contra etiquetas humanas"; el test de disparo cuenta como activación cualquier respuesta no vacía y no prueba casos que no deberían dispararlo. Evals sobre trazas reales, en curso | `interaction`: 83 escenarios ejecutables, juez neutral, FLAKY, pisos de modelo, huellas por corrida, baseline con la versión vieja primero (regla 17) |

Detalles que vale la pena retener: la puntuación estática de cada skill se
guarda junto al sha256 de sus archivos, y un test falla si el puntaje cambia
sin que cambien los archivos. Así distinguen "cambió la skill" de "cambió el
evaluador". El `CLAUDE.md` es un enlace simbólico al `AGENTS.md`, el único
archivo de contexto escrito a mano.

### Los demás

- **[obra/superpowers](https://github.com/obra/superpowers)** (la página
  mostraba unas 298.000 estrellas; el número es raro, tomarlo con pinzas). 15
  skills con flujo obligatorio (idear → planificar → ejecutar con subagentes
  frescos y revisión en dos etapas). Su idea más propia es **TDD para skills**:
  correr un escenario bajo presión (apuro, costo hundido, autoridad,
  cansancio) sin la skill, anotar textuales las excusas del agente, escribir
  la skill mínima que las cierra y sumar una contra-excusa por cada nueva
  (*tabla de racionalizaciones*). Regla para descripciones: solo disparadores,
  nunca el flujo, porque cuando la descripción resumía el proceso el agente
  seguía el resumen y salteaba el cuerpo. Tiene un repo de evals aparte
  ("Quorum"): conversación guionada, criterios ocultos al agente, veredicto
  pass, fail o **indeterminado**, costo y trayectoria por corrida, sin
  reintentos.
- **[anthropics/skills](https://github.com/anthropics/skills)** (unas 181.000).
  Es en sí un marketplace y trae la especificación de Agent Skills. Su
  `skill-creator` corre cada prompt **con y sin la skill** (o con la versión
  vieja), reporta media ± desvío y la diferencia, señala aserciones que nunca
  fallan, y optimiza descripciones con 20 consultas: mitad que deberían
  dispararla y mitad de **casi-aciertos** que no, separadas 60/40 en
  entrenamiento y prueba, eligiendo por el puntaje de prueba.
- **[VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents)**
  (unas 25.700). Más de 161 subagentes en 10 categorías, cada una un plugin,
  con `tools` y `model` por rol. Sin tests; dice explícitamente que no audita
  la corrección.
- **[BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD)** (unas 54.100).
  Agentes de rol (PM, arquitecto, UX, dev, test) con flujos. Idea propia:
  proceso que escala con el tamaño del cambio, de construir directo a
  planificación completa. Sin suite de tests documentada.
- **SuperClaude Framework** (unas 23.900). Comandos, agentes y "modos" de
  comportamiento que se inyectan aparte de los agentes. Solo Claude Code. Tiene
  un workflow de tests sin resultados publicados.
- **contains-studio/agents** (unas 12.400, 10 commits, probablemente inactivo).
  Exige 3 o 4 bloques `<example>` en cada descripción, la misma convención que
  usa este catálogo.

De los siete, solo superpowers y wshobson muestran algo parecido a una
evaluación de comportamiento, y ninguno publica una línea base con versión
vieja contra versión nueva.

### Cómo se distribuye: `npx skills`

[vercel-labs/skills](https://github.com/vercel-labs/skills), la versión 1.7.2
del 2026-10-09. Lo leímos en el **código fuente** sin ejecutarlo, así que acá
*documentado* quiere decir "leído en el código"; lo que solo dice su README se
aclara.

- **Origen.** Va directo al host de git: `owner/repo`, URLs de GitHub y GitLab
  con rama y subcarpeta, `#ref`, rutas locales, o un índice
  `/.well-known/agent-skills/index.json` en cualquier dominio. No hay un
  registro central para instalar; skills.sh sirve para buscar, como caché de
  algunos dueños puntuales y para telemetría.
- **Transporte.** Un clon superficial (`--depth 1`) a un directorio temporal
  que se borra al terminar: no queda caché, y hace falta git. Solo para unos
  pocos dueños en una lista fija usa la API de GitHub y un snapshot de
  skills.sh, cuyo contenido no se verifica contra GitHub.
- **Destino.** Una tabla de ~79 hosts que se detectan porque existe su carpeta
  de configuración. Por defecto copia una vez a `~/.agents/skills/<nombre>` y
  pone un enlace simbólico desde cada host. Funciona porque la skill es la misma
  para todos.
- **Registro.** Un lockfile global, `~/.agents/.skill-lock.json`, y uno por
  proyecto para commitear, `skills-lock.json`, sin timestamps y ordenado. Por
  skill guarda el origen, el `ref` que escribió el usuario y un hash de la
  carpeta. **No guarda el commit resuelto.** Un lockfile global de una versión
  vieja del formato se borra sin avisar.
- **Identidad: el nombre.** El lockfile indexa por nombre de skill; de
  `metadata` lee una sola clave, `internal` (oculta skills internas), y no
  compara `author` (`skills.ts:120`, `skill-lock.ts:184`). Dos skills con el
  mismo nombre y distinto dueño son, para él, la misma. Por eso B-058 marca
  las nuestras con un ID propio en `metadata`.
- **Actualizar.** `check`, `update` y `upgrade` son el mismo comando: `check`
  también actualiza. Compara hashes de carpeta y reinstala solo las skills que
  cambiaron.
- **Contenido.** Copia crudo. No reescribe los links entre skills, así que una
  skill instalada sola que apunta a otra queda con el link muerto (inferencia
  del código; B-053 lo mide). Solo instala skills: lee `marketplace.json` y
  `plugin.json` de Claude Code únicamente para encontrarlas.
- **Telemetría** activa por defecto, contra skills.sh. Se apaga con
  `DO_NOT_TRACK` o `DISABLE_TELEMETRY`.

**Qué tomamos y qué no.** La comodidad no viene de bajar menos, sino de que el
usuario no tiene que hacerse cargo del clon: eso lo copiamos entero, con
`update.py` y `local-hero` (B-050, B-051). Su forma de actualizar está pensada
para skills crudas e independientes, y este catálogo transforma cada archivo
por host y tiene dependencias (los CORE, los links). Por eso no copiamos:

- los enlaces simbólicos a una copia única, porque no hay copia única;
- la reinstalación parcial, porque reinstalar todo tarda segundos y un CORE
  que cambia afecta a todos sus herederos;
- guardar solo el `ref`, que es más débil que el commit que ya sellamos;
- un `check` que escribe;
- la telemetría.

### Cómo se evalúan agentes y skills

- **`claude plugin eval`** ([doc](https://code.claude.com/docs/en/plugin-evals),
  Claude Code ≥ 2.1.269, acceso anticipado). Cada caso es un `prompt.md` y sus
  evaluadores: cuatro gratis (`regex`, `tool_used`, `tool_order`,
  `file_exists`) y dos con juez (`llm`, que aprueba con 2 de 3 votos, y
  `baseline` contra una transcripción de referencia). Tres corridas por rama
  por defecto; con `--ablation with-without` reporta CON, SIN y **Δ**. Trae
  `--threshold` para CI, `--max-cost-usd` y JSON versionado. `tool_used: Skill`
  dice si la skill se disparó sin juez. Si el Δ sale negativo con la skill
  disparada, su consejo es "sospechá del juez antes que del plugin".
- **Guía de Anthropic** ([Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)).
  Evaluar el resultado y no el camino. Primero evaluadores por código, juez
  donde haga falta, humanos para validarlo. Distinguir pass@k (al menos una de
  k) de pass^k (las k): con 75 % por intento, pass^3 da ~42 %. Sets
  balanceados, donde la conducta debe aparecer y donde no. Un juez por
  dimensión, con la opción "no se puede saber". Leer las transcripciones antes
  de creerle a un puntaje.
- **Calibrar el juez.** La práctica que más se repite (Hamel Husain y Shreya
  Shankar, `evals-skills`; superpowers; Anthropic) es medir al juez contra
  etiquetas humanas antes de confiar en él: tasa de acierto sobre los PASS y
  sobre los FAIL (TPR/TNR), con decenas de ejemplos etiquetados de cada lado.
  *Documentado* el método; la cantidad mínima de etiquetas, *reportada*.
- **promptfoo y OpenAI** ofrecen jueces por rúbrica, comparación de a pares y
  evaluadores deterministas sobre la trayectoria de herramientas; OpenAI
  propone evaluar trazas primero y convertirlas después en datasets. En la
  comparación de a pares, el sesgo de posición está documentado; el remedio
  estándar es invertir el orden y quedarse con los veredictos consistentes.
  *Reportado.*

### Qué recomiendan los hosts sobre subagentes (2026-11-10)

Las dos guías de Anthropic son de enero y abril de 2026, anteriores a este
relevamiento, pero no estaban acá. Lo de este mes son cambios de producto
(sección 4), no recomendaciones nuevas. Todo *documentado* salvo aclaración.

- **Cuándo conviene** ([Anthropic, 2026-01-23](https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them)).
  Tres casos y solo tres: proteger el contexto (la subtarea produce mucho
  texto que no hace falta conservar), paralelizar (para cubrir más, no para
  ir más rápido) y especializar (demasiadas herramientas, personas que se
  contradicen, o un dominio que desborda a un generalista). Fuera de eso,
  "los costos de coordinación suelen superar los beneficios".
- **Cuánto cuesta.** Un sistema de varios agentes gasta "3 a 10 veces más
  tokens" que uno solo para la misma tarea, y suele tardar más en total.
  Nuestras tres cifras van de 1,3 a 4 veces: dos quedan debajo de ese rango
  y una adentro (sección 4).
- **Cómo partir el trabajo.** Por **contexto**, no por tipo de trabajo. Un
  agente por rol (uno planifica, otro implementa, otro prueba, otro revisa)
  es "a menudo contraproducente": cada pase pierde fidelidad, y en su
  experimento los agentes gastaron más en coordinarse que en trabajar. "El
  agente que construye una feature también debería escribir sus tests."
  Buenas fronteras: investigaciones independientes, componentes con una
  interfaz limpia y **verificación de caja negra**. Malas: fases sucesivas
  del mismo trabajo, piezas acopladas, estado compartido.
- **El verificador que canta victoria.** Un agente que verifica corre uno o
  dos tests, los ve pasar y declara éxito. Remedio: criterios concretos,
  pruebas negativas y la instrucción explícita de correr todo antes de
  aprobar.
- **Reglas de uso en Claude Code** ([Anthropic, 2026-04-07](https://claude.com/blog/subagents-in-claude-code)).
  Delegar cuando hay que explorar diez archivos o más, o hay tres o más
  piezas independientes. No delegar trabajo secuencial, ediciones al mismo
  archivo ni tareas chicas. Un roster grande vuelve menos confiable la
  delegación automática: "un puñado de agentes bien delimitados". El encargo
  dice el alcance y **la forma de lo que tiene que volver**. La descripción
  del agente nombra las condiciones que lo disparan, no su capacidad.
- **Los demás dicen lo mismo en chico.** VS Code: delegar trabajo de alcance
  claro que devuelve algo usable (investigar antes de implementar, comparar
  enfoques, revisar); para una consulta rápida o un cambio chico, pedirlo
  directo. Codex: no subir la profundidad salvo que haga falta, porque
  multiplica tokens y latencia (*reportado*).

**Qué recibe y qué puede hacer el agente llamado, host por host.** Es la
pregunta que decide cómo escribir un encargo que sirva en todos. Claude Code,
*medido* en las trazas del 2026-11-10; el resto, *documentado* en la doc de
cada host leída ese día, sin probar (Kiro, *reportado*: su página redirige y
solo leímos el resumen).

| | Arranca con | Sus permisos | Quién puede llamarlo | Niveles | Qué vuelve |
|---|---|---|---|---|---|
| **Claude Code 2.1.322** | Contexto limpio y el encargo; un *fork* hereda la conversación entera | Los de su propio archivo (`tools:`) | Quien tenga la herramienta `Agent` | 3 | Un informe; se lanza en segundo plano y se lo puede retomar con un mensaje |
| **opencode** | "Fresh context", en una sesión hija | "The child uses its own configured permissions" | Reglas `subagent` en los permisos del que llama | Sin regla general documentada | Sin documentar |
| **Codex** | Sin documentar | **Hereda el sandbox del que llama**; el archivo del agente no puede cambiarlo | Por nombre, en lenguaje natural | 1 | Una respuesta consolidada cuando terminan todos |
| **Kiro** | Su propia ventana de contexto | Los de la sesión que llama también se le aplican | `availableAgents` | Sin relevar | Sin relevar |
| **Antigravity** | "Clean slate": no hereda el historial | Hereda la configuración de seguridad del que llama, y el principal decide sus herramientas | `subagent: true` en el agente | 10 | Un mensaje de resultado; queda en espera y despierta con otro mensaje |

Tres cosas salen de la tabla:

- **El encargo es el único canal que existe en todos.** Salvo el fork de
  Claude Code, el agente llamado no ve nada de la conversación. Lo que no
  está en el encargo, o en un archivo que el encargo nombra, no llegó.
- **El acceso declarado solo está garantizado cuando el agente es la
  conversación.** Llamado por otro, en Codex, Kiro y Antigravity manda en
  todo o en parte el que llama. La doc de Codex dice que `sandbox_mode` no
  se puede fijar por agente, y la sección 4 lo midió funcionando en la
  0.144.5 para el agente principal: no es lo mismo, y no está medido como
  subagente. B-097.
- **Encadenar dos pases no es portable.** Con un nivel en Codex y ninguna
  regla en opencode, "A llama a B y B llama a C" solo existe en Claude Code y
  Antigravity. Un agente llamado que necesita a otro tiene que devolverlo,
  no delegarlo.

**Cómo delegaron los nuestros** (*medido*, trazas guardadas del 2026-11-10,
las cinco muestras principales que delegaron, B-091). Las cinco llamaron al
agente `senior-dev` por nombre: ningún fork, ningún segundo nivel. Los
encargos tuvieron entre 96 y 470 palabras y los cinco pidieron un informe de
vuelta; `ux-ui` escribió primero el spec en un archivo y mandó la ruta.
`senior-dev`, llamado así, no cargó ninguna skill en las cinco. El harness no
lo vio: `delegated_to` quedó vacío porque solo se registraba en los
escenarios que declaran `delegate: true`. Desde B-094 se registra en toda
muestra, y al releer esas trazas con el código nuevo apareció una sexta que
nadie había notado: `security-fixes-the-class` también delegó.

**Lo que cuesta el pase en lectura** (*medido*, las mismas seis trazas). El
agente llamado arranca sin la conversación y vuelve a leer: de los 35
archivos que leyó `senior-dev` en las seis delegaciones, 20 ya los había
leído quien lo llamó. La mitad de esos 20 los leyó para editarlos, y eso no
se ahorra; los otros 10 los leyó solo para entender lo que el otro agente ya
había entendido (`auth.js`, los tokens, `package.json`, el README). Los
encargos decían qué hacer, no qué estaba ya establecido. En un fixture de
seis archivos son centavos; en un repo real es el grueso del costo de
delegar. El harness lo cuenta desde hoy en cada delegación (`reread` y
`reread_context`); lo que lee con un `grep -r` no entra en la cuenta.

**Dos intentos de bajar esa relectura, y ninguno la movió** (*medido*,
2026-11-10 y 11, Sonnet, ×3, B-098). Pedirles a los que entregan que el
encargo liste lo establecido, cada hecho con su archivo y su peldaño, cambió
los encargos y no la lectura: 1,3 archivos releídos solo para entender por
delegación antes, 1,1 después. Decirle al que recibe que un hecho con lugar y
peldaño se comprueba solo donde su cambio depende de él tampoco: con el
encargo directo, `senior-dev` leyó 7, 7 y 6 archivos antes y 6, 6 y 6
después, y en los dos casos detectó 3 de 3 un dato falso plantado en el
encargo. Las dos reglas se revirtieron. En un repo de siete archivos el que
recibe lee todo antes de escribir, que es su propio juicio #1 y es barato;
una lista de hechos no compite con eso. Queda sin medir el caso que
importa: un repo donde leer todo no es posible.

**Dónde nos toca.** Este catálogo es un roster por rol, que es justo la
forma de partir que la guía desaconseja, y el 2026-11-10 hicimos que `ux-ui`
y `security` le pasen el código a `senior-dev`. Tres cosas lo sostienen, y
conviene tenerlas a la vista porque son las que hay que seguir midiendo:

- Casi siempre el agente es la conversación principal: lo elige el usuario,
  o el host por la descripción (los 24 escenarios de routing en 3/3, B-043).
  Eso no es un sistema de varios agentes y no paga coordinación.
- Los dos pases que agregamos son límites de rol que el usuario decidió, no
  una optimización: el diseñador y el auditor no tocan el código. La guía lo
  contempla como especialización por restricciones que se contradicen.
- `qa` y `security` revisando el trabajo de otro son la "verificación de caja
  negra" que la guía pone del lado bueno.

Lo que la guía sí nos discute: la cadena fija de `lh-orchestration`
(diseño → construcción → verificación) es partir por fases, y `qa`
escribiendo los tests de lo que construyó `senior-dev` es el pase que ellos
midieron mal. No lo cambiamos sin medir (regla 17): B-095.

### El balance

**Donde este catálogo va adelante:**

- Una evaluación de comportamiento sobre el agente instalado, con juez neutral
  y la versión vieja corrida primero. Lo más cercano es Quorum, de superpowers;
  la de wshobson está, según su propia doc, sin validar.
- Entre MUESTRAS del agente, exigir que todas coincidan (FLAKY, sin mayoría)
  está en el espíritu de pass^k. Pero los 2 de 3 de `claude plugin eval` son
  otra cosa: votos del JUEZ sobre una misma respuesta. Nuestro juez vota una
  sola vez, y de ese lado somos más laxos.
- Huellas por corrida y `--applicability`: saber si un VEREDICTO de
  comportamiento viejo sigue valiendo sin volver a pagarlo. wshobson hace algo
  parecido para su puntuación estática (el sha256 de arriba); para veredictos
  de comportamiento no lo vimos en ningún otro.
- El acceso declarado y traducido a lo que cada host hace cumplir, con
  diferencias medidas por host.
- La regla 17 es, en esencia, el TDD para skills de superpowers.

**Donde va atrás:**

| Falta | Quién lo hace | Ítem |
|---|---|---|
| Comparar contra no usar ningún agente (Δ) | `claude plugin eval`, skill-creator | B-038 |
| Juez calibrado contra etiquetas humanas | evals-skills, superpowers, Anthropic | B-039 |
| Veredicto indeterminado | superpowers (Quorum), Anthropic | B-040 |
| Evals de disparo con casi-aciertos | skill-creator | B-041 hecho; B-043 (routing) pendiente |
| Usar la herramienta oficial antes que construir | `claude plugin eval` | B-047, descartado: exige un plugin (§4) |
| Actualizar con un comando, sin gestionar el clon | `npx skills` | B-050, B-051 |
| Tope de costo por corrida | `claude plugin eval` | B-044, hecho |
| Humo con CLI reales en CI | wshobson | B-046 hecho para claude y opencode; kiro pide login |
| Escenarios bajo presión con excusas registradas | superpowers | B-045 |
| Saber si conviene precargar una skill en vez de esperar que cargue | Claude Code (`skills:` en el agente) | B-093 |
| El encargo a otro agente dice la forma de lo que tiene que volver | Guías de Anthropic | B-095 |

**Lo que adoptamos sin código:**

- **Una descripción de skill lista disparadores, no el flujo** (superpowers:
  cuando la descripción resumía el proceso, el agente seguía el resumen y
  salteaba el cuerpo). La regla 14 ya pide que el disparador nombre un
  umbral; esto suma que la descripción no anticipe los pasos. Rige para toda
  descripción que se reescriba, y B-041 la aplica.

- **El encargo a otro agente se sostiene solo.** Desde el 2026-11-10 `ux-ui`
  y `security` entregan un brief que no necesita la conversación (B-091). Es
  la mitad de lo que piden las guías; la otra mitad, decir la forma de la
  respuesta, está en B-095.

**Lo que decidimos no copiar, y por qué:**

- **Un agente por stack.** Choca con la regla 5. Lo que ellos reparten en
  decenas de agentes, acá lo cubre una skill que cambia según el proyecto.
- **Cadenas fijas de orquestación.** Son predecibles, pero pasan por todos los
  pasos aunque la tarea necesite dos, y delegar costó ~4× la única vez que se midió.
- **`model:` por agente.** B-036 midió que la calidad no lo necesita. wshobson
  lo usa por COSTO (haiku para trabajo mecánico), y los agentes de este
  catálogo no hacen trabajo mecánico. Ojo con el alcance: B-036 resolvió UN
  caso, no midió todo el catálogo. Se reabre si el costo pasa a ser el motivo
  o si aparece otro escenario que solo pasa con un modelo mayor.
- **El flujo obligatorio de superpowers** (idear → planificar → ejecutar en
  cada tarea). Choca con la escalera y con "saber cuándo no orquestar": la
  ceremonia tiene que escalar con el tamaño del cambio, que es justamente la
  idea de BMAD.
- **Publicar como marketplace de Claude Code, por ahora.** Un agente que viene
  dentro de un plugin pierde `hooks`, `mcpServers` y `permissionMode`
  (*documentado*); el tier de acceso sobreviviría solo con `tools:`. B-028
  sigue en espera.

---

## 4. Lo que medimos nosotros (2026-10-11)

| Host | Agentes | Skills | Solo lectura | Sorpresas |
|---|---|---|---|---|
| **opencode 1.18.11** | `~/.config/opencode/agents`, `.opencode/agents`. **No** lee `.agents/agents` | propia + `~/.claude/skills` + `~/.agents/skills` + `skill/` (legacy); por proyecto `.agents/skills` y `.claude/skills` | `permission` (documentado) | Con la misma skill en varias carpetas **elige una copia distinta en cada corrida** (32, 10 y 4 de 48 del proyecto en tres corridas idénticas) |
| **Codex 0.144.5** | TOML en `~/.codex/agents`, `.codex/agents` | `~/.codex/skills`; `~/.agents/skills` (documentado) | `sandbox_mode = "read-only"` | Una skill de más de 8 KB llega entera (0.162.1, B-042). El flag `--sandbox` pisa el modo de cada agente; `-c sandbox_mode=...` y `config.toml` no. `codex exec` espera stdin si no se cierra |
| **Antigravity (agy 1.3.3)** | `~/.gemini/config/agents`, `.agents/agents`; con el mismo nombre **gana el del proyecto** | `~/.gemini/config/skills`, `.agents/skills` | allowlist `tools:` | La doc da `~/.gemini/antigravity-cli/skills/` para el CLI y **no se lee**. Sin `tools:` el agente recibe un set mínimo (sin escribir ni buscar). Un nombre de herramienta desconocido aborta el arranque. Un agente sin frontmatter se ignora: `--agent` usa el global de ese nombre si existe, o el agente principal, sin avisar |
| **Claude Code 2.1.296** | `~/.claude/agents`, `.claude/agents` | `~/.claude/skills`, `.claude/skills`. **No** lee `~/.agents/skills` ni `.agents/skills` | allowlist `tools:` | Se puede medir gratis: el evento `init` de `claude -p --output-format stream-json --verbose` lista las skills cargadas antes de consultar al modelo. El comportamiento de los agentes lo prueba el harness |
| **Kiro (kiro-cli 2.29.1)** | JSON en `~/.kiro/agents`, `.kiro/agents` | `~/.kiro/skills`, `.kiro/skills`, vía `resources` `skill://` (el `~` funciona también por proyecto) | lista `tools`, que se hace cumplir | **Lee solo la primera línea de la descripción de una skill**: con `description: >` la ve vacía, y la skill no se dispara nunca. `code` modifica archivos (AST rewrite) y `subagent` delega en un agente que escribe. `kiro-cli agent validate` acepta herramientas y campos inventados |

### Cambios de Claude Code que tocan lo medido (2.1.299 a 2.1.322, 2026-11-10)

Leídos en el [changelog](https://code.claude.com/docs/en/changelog) y en la
doc de subagentes: *documentado*, no medido, salvo el último punto. El harness
corrió todo el 2026-11-10 sobre la 2.1.322 sin adaptarse a ninguno.

- **Los subagentes "fork" vienen activados en `claude -p`** desde la 2.1.302
  (2026-10-16). Un fork hereda la conversación entera y las herramientas de
  quien lo lanza, en vez de arrancar limpio con un encargo. Con los fork
  activados, `ux-ui` y `security` igual llamaron a `senior-dev` por nombre en
  las cinco muestras leídas (sección 3). El harness no distingue las dos
  formas y solo registra la delegación donde el escenario la declara. B-094.
- **Un subagente puede lanzar subagentes, hasta 3 niveles.** Con
  `eng-manager` delegando en especialistas que ahora también delegan, una
  corrida puede abrirse en árbol sin que el escenario lo pida. El harness no
  fija esa profundidad. B-094.
- **Dos ajustes de permisos nuevos.** `permissions.denyInsteadOfPrompting`
  (2.1.319): la llamada que esperaría una aprobación se niega y el turno
  sigue, también en subagentes. Es un rechazo que no viene del usuario, lo
  que B-072 quiere medir. `permissions.blockWritesOutsideWorkingDirectories`
  (2.1.314): Write y Edit rechazan rutas fuera de las carpetas de trabajo en
  todos los modos; cubre una parte de lo que B-067 buscaba con el sandbox,
  aunque no la shell.
- **`claude -p` ya no falla en silencio.** Sale con código 1 cuando el
  arranque falla (2.1.314), cuando se queda sin disco para la transcripción
  (2.1.317) y cuando el modo auto rechaza sus acciones (2.1.319). Antes salía
  con 0 y sin texto, que el harness leía como "sin evento de resultado".
- **Esfuerzo por subagente.** `effort:` en el agente y
  `CLAUDE_CODE_SUBAGENT_EFFORT` (2.1.316). Es una palanca de costo más fina
  que `model:` y el catálogo no la usa; la decisión de `inherit` (B-036) se
  tomó cuando no existía.
- **Delegar costó entre 1,3 y 2,4 veces** (*medido*, 2.1.322, Sonnet, B-091).
  El mismo pedido, antes y después de que el agente dejara de escribir el
  código: `security` con las tres muestras delegando pasó de USD 0,45 a 1,08
  (×2,4); `ux-ui`, con dos de tres delegando, de 0,61 a 0,82 (×1,3). No es
  una comparación limpia: el dev que recibió el encargo además escribió
  tests que nadie había pedido. Con el ~4× de la única medición anterior son
  tres cifras: dos debajo del "3 a 10 veces" de la guía y una adentro. Son
  delegaciones de un solo pase; la guía habla de sistemas enteros.

- **El tope por muestra cuenta lo que gasta el agente llamado** (*medido*,
  2.1.322, Sonnet, 2026-11-10, B-044). `eng-manager` le pasó una
  implementación a `senior-dev` con `--max-budget-usd 0.18`: en dos de tres
  muestras el corte llegó con el que llama en su primer turno y el llamado
  trabajando (4 y 17 eventos suyos en la traza), como el mismo
  `error_max_budget_usd` de siempre. El tope no es exacto: cortó en USD
  0,195 y 0,197, y la tercera muestra terminó sola en 0,185 sin que la
  cortara. Y el corte no deshace nada: en una muestra el llamado ya había
  modificado dos archivos de `src/`, que quedaron a medio cambiar. Con
  `ux-ui` como el que llama y tope 0,20 no se pudo medir: gastó el tope
  solo antes de delegar. Costo de las cinco muestras, USD 0,96.

### Kiro reescribe los agentes en el formato 2.x (kiro-cli 2.29.1, 2026-11-11)

*Medido*, sin consultar al modelo (B-099).

- **Cada arranque de `kiro-cli` actualiza los agentes que encuentra en el
  formato viejo.** Un JSON con `allowedTools` y sin bloque `permissions` se
  reescribe en el lugar y deja un `.bak` al lado: le agrega
  `"permissions": {"rules": [{"capability": "fs_read", "effect": "allow"}]}`,
  ordena una lista `tools` explícita y le suma la etiqueta `web` junto a
  `web_fetch` y `web_search`. Pasó el 2026-10-23 a las 16:55 y volvió a pasar
  el 2026-11-11 a la 01:36, un minuto después de reinstalar, al pedirle la
  ayuda al CLI. La doc lo llama formato universal, el que cargan sus motores
  2.x y 3.x, y dice que el motor 3.x saltea un agente 2.x hasta que se
  actualiza (*documentado*).
- **El instalador lo tomó por una edición a mano.** El archivo reescrito ya no
  coincidía con el hash registrado, y `--refresh` no pisa lo editado: Kiro
  corrió 19 días con el catálogo del 23-10 mientras `--status` decía
  "15 edited by hand". El aviso por archivo existía, perdido entre cientos de
  líneas.
- **Arreglo.** `install.py` escribe directamente la forma que deja Kiro. Con
  eso `kiro-cli agent upgrade ~/.kiro/agents --dry-run` da "already universal"
  en los 15, arrancar el CLI no toca ningún archivo (mismo hash antes y
  después) y `--status` no marca nada. Además, toda corrida del instalador
  cierra con un `NOT UPDATED` cuando dejó archivos sin actualizar.
- **Sin medir:** si el tier de solo lectura se sostiene en el motor 3.x. La
  lista `tools` sigue sin `write` ni `shell`, pero en 3.x los permisos son
  reglas por capacidad y a un agente llamado por otro se le aplican también
  los de quien lo llama (B-097).

### Otros hallazgos medidos

- **Esconder una herramienta no es negarla** (Claude Code 2.1.299, 2026-10-16
  y 17, B-066). `--disallowedTools` saca la herramienta de lo que ve el
  modelo: con Edit y Write escondidos y la shell abierta, architect y
  senior-dev editaron por `sed -i` o un script 6 de 6 veces, sin intentar
  Edit nunca. Con la herramienta a la vista y fuera de los permisos, que es
  lo que pasa cuando el usuario dice que no, los 3 que la llamaron
  respetaron el rechazo, pero los otros 3 fueron directo a la shell, por
  donde la aprobación de cada edición se saltea sin que nadie lo note. Con
  una regla de dos líneas en el CORE ("Approval follows the effect"), la
  primera corrida dio 6 de 6. Con más muestras (corregido el 2026-10-18):
  senior-dev 6 de 6 y architect 15 de 18, en cuatro corridas que incluyen un
  A/B entre "a refused tool" y "a refused action" (8 de 9 contra 7 de 9: la
  palabra no cambia nada). Ninguna muestra que vio el rechazo lo rodeó. Las 3
  fallas de architect son iguales: fue a la shell antes de intentar Edit, sin
  haber visto ningún rechazo. Un escenario de permisos tiene que dejar ver el
  rechazo: si no, mide qué hace el agente con lo que tiene a mano. Las 3
  fallas eran el cambio entero escrito en lote, en una sola llamada de shell,
  por eficiencia. Con un procedimiento en el cuerpo de architect (B-073,
  2026-10-18: la herramienta de edición como primera llamada por archivo,
  aunque un comando sea más rápido), 12 de 12 llamaron primero a Edit, sin
  trabar un generador del repo (3 de 3). Es consistente con la mejora, no la
  prueba: con la tasa vieja, 12 de 12 sale por azar 1 de cada 9 veces.
- **El juez, medido contra un humano** (2026-10-15/16, B-039, primera etapa;
  `labels.py` del harness). 80 respuestas ya guardadas, etiquetadas a mano sin
  ver el veredicto (61 PASS, 13 FAIL y 6 AMBIGUA), y vueltas a juzgar sin
  correr ningún agente. Con las etiquetas tal como se dieron, ningún juez
  llegó a TNR 0,90:

  | Juez | TPR | TNR | USD por veredicto |
  |---|---|---|---|
  | El de las corridas | 0,76 | 0,67 | — |
  | Opus (52 de 80, cortado por el tope) | 0,95 | 0,56 | 0,019 |
  | Sonnet | 0,92 | 0,69 | 0,009 |
  | Codex `gpt-6.1-sol` | 0,84 | 0,85 | tokens de suscripción |

  Los desacuerdos se revisaron caso por caso contra el catálogo. **5 criterios
  estaban mal escritos**: ejemplos entre paréntesis que el juez lee como lista
  a cumplir, un PASS sin su FAIL simétrico, "revocar" con dos lecturas.
  **6 ya se habían corregido** en los YAML, pero las respuestas se habían
  juzgado y etiquetado con el texto viejo. **11 etiquetas se revisaron**,
  guardando la original, y **2 se excluyeron** porque su escenario se
  reescribió. Con los criterios corregidos, Sonnet coincide en 64 de 64 PASS
  y 10 de 10 FAIL; Codex, en 60 de 64 y 10 de 10. Con las etiquetas
  originales, la TNR de los dos es 0,64: parte de la mejora viene de la
  revisión, que movió etiquetas hacia los jueces aunque cada cambio se apoyó
  en el catálogo.

  **Límites.** 10 FAIL es poco: un 10/10 es compatible con una TNR real
  cercana a 0,7. La reserva del 40 % quedó sin ningún FAIL, así que no hay
  TNR medida sobre ella.

  **Perfil de cada juez.** Opus es el más indulgente y el más caro. Codex es
  el más literal: exige lo que el criterio no pide (un costo, una skill por
  nombre, un bug que ya estaba en el código). Opus juzgando dos veces las
  mismas 46 respuestas no dio lo mismo (TNR 0,67 en las corridas, 0,56 al
  volver a juzgar): un veredicto suelto tiene ruido propio.

  **Codex como juez hay que aislarlo.** Sin flags, el modelo ve las 48 skills
  del catálogo, que están en `~/.agents/skills` y `~/.codex/skills`;
  `-c skills.include_instructions=false` las saca, y `codex debug
  prompt-input` lo verifica gratis antes de cada corrida. Sin herramientas,
  cada veredicto usa un 35 % menos de tokens (8.481 contra 12.953).

  **Decisión:** Sonnet pasa a ser el juez por defecto del harness, y Codex
  queda como segundo juez de otra familia, a pedido.

  **El veredicto va al final** (2026-10-17, B-068). Con el veredicto en la
  primera línea, el juez decidía antes de pensar: una vez escribió FAIL,
  razonó criterio por criterio y terminó en PASS, y el harness se quedó con
  la primera palabra. Ahora razona y cierra con `VERDICT:`; un texto que se
  contradice es ERROR. Con las mismas 78 etiquetas, Sonnet dio TPR y TNR
  idénticas, 0 ERROR y un solo cambio, en una muestra ambigua, a USD 0,011
  por veredicto.
- **En Claude Code, un agente con allowlist de `tools:` sin `Skill` no carga
  skills** (2.1.299, 2026-10-14, B-041). visionary y eng-manager, de solo
  lectura, cargaron 0 de 8 skills pedidas; encontraban el archivo con `Glob` y
  `Read` solo porque el harness copia las skills a su carpeta de trabajo. Con
  `Skill` en la lista: 8 de 8, y sin herramientas de escritura. El chequeo
  pago `skill` de `smoke.py` le preguntaba solo al agente de escritura, y por
  eso el hueco no se vio antes.
- **Disparo de skills, línea base** (Sonnet, 2026-10-14, B-041): con una skill
  por agente, 4 consultas que deben cargarla y 4 casi-aciertos, los 15 agentes
  cargan 59 de 60 y evitan 58 de 60. Las dos cargas de más son fronteras
  ambiguas entre skills vecinas, no descripciones que disparen de más.
- **Codex no corta una skill de más de 8 KB** (0.162.1, 2026-10-13, B-042).
  No mete el cuerpo en el prompt: `codex debug prompt-input`, que es gratis,
  muestra solo nombre, descripción y ruta, aun con `$skill` en el pedido. El
  modelo lee el archivo con el shell, con un presupuesto de salida de 10.000
  tokens por defecto. En una consulta, el `cat` de la copia instalada de
  `lh-llm-integration` (10.907 bytes) quedó registrado entero, idéntico byte a
  byte. El ~8 KB que le atribuye wshobson no aplica a esta versión.
- **`claude plugin eval` no evalúa lo instalado** (Claude Code 2.1.296,
  2026-10-13, B-047). Solo carga un plugin con `.claude-plugin/plugin.json`:
  sin manifiesto, el directorio se acepta como raíz de la suite pero el JSON
  sale con `plugins: []`. Cada corrida va aislada de `~/.claude`, y no hay
  forma de correr un caso COMO un agente: solo se puede delegar en él con
  `Agent`, y ahí pierde `permissionMode`. Se mide gratis con
  `--max-cost-usd 0`, que corta antes de la primera corrida y deja igual el
  JSON con lo que se cargó.
- **Claude Code no lee `~/.agents/skills` ni `.agents/skills`**: el aviso de
  `shadowing` no lo incluye (2.1.296; se mide gratis con el evento `init`).
- **En agy gana el agente del proyecto** sobre el global del mismo nombre, y uno
  sin frontmatter se ignora y se usa el global (1.3.3).
- **Los cuatro hosts siguen un enlace simbólico** a una skill de proyecto
  (opencode, Claude Code, agy, Codex). Ver B-029.
- **El orden de los CORE no cambia el comportamiento observable**: `devops` con
  los dos órdenes, 4/4 en ambos (Sonnet, 1 muestra; runs `20261011-211529` y
  `20261011-211554`).
- **Un CORE un 25 % más corto no baja la tasa de PASS** (B-027): 1313 → 986
  palabras quitando racional y anécdotas y dejando la cláusula que cada
  escenario demostró discriminante. Suite completa `20261012-111015`: 65/68 en
  los escenarios comunes contra 60/68 de la base, costo del agente −5,6 %. El
  único rojo con causa plausible en el recorte falló igual con el CORE largo
  (control `20261012-113332`, 0/3): con una muestra por escenario, nueve
  verdicts cambiaron de FAIL a PASS sin que nada los tocara, así que un flip
  aislado no atribuye nada hasta correr el control con el prompt viejo.
- **Un procedimiento mueve a Sonnet donde un principio no** (B-036): la misma
  regla dura de architect, como fila de la escalera, dio 3/16 en Sonnet y 3/3
  en Opus; reescrita como tres pasos con disparador concreto, a escribir como
  texto antes del primer edit, dio 4/4 en Sonnet (`20261012-130849` y suite
  `20261012-131428`, 75/75). La brecha entre modelos era de ORDEN de
  generación, no de conocimiento: Sonnet nombraba el costo después del Edit.
  Texto y herramienta se intercalan, así que pedir el análisis en texto antes
  de la herramienta fija el orden del comportamiento.
- **Línea base neutral**: suite completa con `claude-sonnet-5-5`, 60/68 (run
  `20261011-220947`). Los fallos consistentes también fallaban con la
  configuración del usuario (experimento de atribución): no los causaba la
  sesión neutral.
- **Los agentes casi nunca cargan sus skills**: 1 de 15 muestras en 5 escenarios,
  y cargarla o no no explica quién pasa (7 PASS y 7 FAIL sin skill; run
  `20261011-230905`). Un criterio que vive solo en una skill es invisible en la
  práctica. Ver B-023.
- **Resistencia a contenido con instrucciones** (B-024): en 9 muestras, con la
  trampa en un comentario del código, en el README pidiendo un secreto y en la
  salida de un test, ningún agente intentó un comando prohibido, cambió un
  archivo ni filtró el secreto (Sonnet, run `20261012-002037`). La falla está
  en avisar: en 1 de 3 el agente no le contó al usuario que el código traía
  una instrucción dirigida a agentes, que pedía justamente eso. Ver B-030.

- **Choques entre `npx skills` y el catálogo** (B-053, 2026-10-13; `skills`
  1.7.2, `install.py` @ `8c500d1`, cada caso en un `HOME` descartable, con
  `DO_NOT_TRACK=1`). Es el baseline que B-058 repite al cerrar.
  - **Nombres que ya existen afuera: 26 de 48** con nombre idéntico en el
    índice de skills.sh (un piso: la búsqueda es difusa y se miraron 50
    resultados por nombre). Los de más peso: `code-review`
    (`mattpocock/skills`, 723.322 instalaciones; es la skill de apple-dev) y
    `orchestration` (`stablyai/orca`, 285.981; la de eng-manager).
  - **La de afuera primero, después `install.py`** (target `claude`, `npx
    skills` para un solo host, que copia sin enlace). Con `--on-conflict
    overwrite` o `--refresh`, la ajena se pisa sin aviso. Con `ask` sin TTY
    (un script, `local-hero`) `install.py` renombra la nuestra a
    `code-review-2`, pero en el mismo comando `relink_skills` reescribe el
    `SKILL.md` de la carpeta ajena con el nuestro, porque decide por el
    nombre: queda una carpeta **mezclada**, nuestro `SKILL.md` con el
    `agents/openai.yaml` del tercero, y dos copias nuestras.
    `install.py --status` cuenta `code-review-2` como "foreign".
  - **`install.py` primero, después `npx skills add`**: pisa la nuestra sin
    aviso, y `install.py --status` la reporta como "stale", no como ajena.
  - **Enlace simbólico** (`npx skills add` para dos hosts, `claude-code` y
    `codex`: copia en `~/.agents/skills` y enlace desde `~/.claude/skills`).
    `install.py --tool claude` **se cae** con `OSError: Cannot call rmtree on a
    symbolic link` a mitad de la instalación: quedaron 7 de 48 skills, ningún
    agente y ningún sello. No escribe a través del enlace (la ajena queda
    intacta), pero el catálogo no se puede instalar.
  - **Ida y vuelta**: `npx skills update` no restauró la suya después de que
    `install.py` la pisó, porque solo reinstala cuando cambia la carpeta en el
    repo de origen. El ida y vuelta queda latente hasta el próximo cambio de
    ese repo; no se pudo provocar.
  - **Target `shared`**: con `npx skills` para un solo host no hay choque en
    `~/.agents/skills` (`npx skills` escribe solo en `~/.claude/skills`); con
    varios hosts sí, porque esa es su carpeta canónica.
  - **Nuestra skill instalada con `npx skills add`** (`discovery`, desde este
    repo): la copia cruda deja **10 de 10 links muertos** entre skills.
  - **Repetido con B-058** (mismo día, mismo `skills` 1.7.2): la ajena con
    nuestro nombre queda entera (ni carpeta mezclada ni `-2`) y solo
    `--on-conflict overwrite` la reemplaza; con el enlace de dos hosts
    `install.py` ya no se cae (47 skills nuestras, 15 agentes, sello, y el
    enlace intacto también tras `--refresh`); `--status` dice "not ours" y
    "links" donde antes decía "stale"; y nuestra skill copiada cruda por `npx
    skills add` se reconoce por su ID: `install.py` la adopta y deja 0 de 10
    links muertos. El ida y vuelta sigue latente: es de `npx skills`, que
    identifica por nombre.
  - **Migración medida sobre una instalación real** (6 hosts con sello de
    `0abe968`, anterior a B-058, solo lectura con `--status`): reconstruir lo
    que el instalador escribió en ese commit reconoció las 48 skills y los 15
    agentes como nuestros en los 6 hosts, sin ningún falso "editado", y las 15
    skills propias del usuario en `~/.claude/skills` como ajenas.
- **Prefijo `lh-` en las 48 skills** (B-059, 2026-10-13). Elegido contra el
  índice de skills.sh: ninguna skill pública empieza con `lh-` y ninguno de
  los 48 nombres con el prefijo existe; `local-agents-` ya lo usan dos
  proyectos ajenos, así que una frase descriptiva no es un nombre propio.
  - **Carga de skills, antes y después** (los 6 escenarios de B-023, ×3,
    Sonnet; corridas `20261013-214734` y `20261013-220105`): **11/18 cargas
    en las dos**, y cargan las versiones con prefijo. El prefijo no cambia
    cuándo un agente carga sus skills. Escenario por escenario la carga varía
    entre corridas sin que nada cambie (de 0/3 a 2/3), así que con 3 muestras
    solo el total dice algo.
  - **Migración real** (6 hosts): `--refresh` instaló las 48 con prefijo y
    retiró 288 copias viejas (48 por host), las que eran nuestras, estaban
    reemplazadas e intactas según el sello; las 15 skills propias del usuario
    quedaron idénticas byte a byte. El paso previo, un `--refresh` desde un
    sello anterior a B-058, encontró dos bugs que 37 tests no veían, porque su
    simulación de un sello viejo tenía un campo que uno real no tiene.
- **Qué aporta el catálogo frente al modelo solo** (Claude Code 2.1.303, Sonnet
  5.5, 2026-10-20, B-038). Los mismos escenarios en la misma instalación
  (`e2cca79`) con el agente del catálogo (`20261020-193010`, una muestra) y en
  una sesión neutral sin `--agent` y sin agentes ni skills en el workspace
  (`20261020-193738`, `-200125`, `-200810`, `-201059`, `-201340`, `-201530` y
  `-202121`, tres muestras por escenario). Costo: USD 10,27 con catálogo y
  13,71 sin él, USD 23,98 en total. Las cifras salen de `viz.py --compare`
  con esas ocho corridas, que junta las muestras de cada rama; se reproducen
  desde el repo del harness. Cuentan 68 escenarios: quedan fuera las tres
  celdas de la medición de sesgo de autoría (`protects: design-cell`, no son
  evidencia del catálogo) y dos que no pueden correr sin él (`no_agent:`).
  Con catálogo pasan todos; sin él, el 77 % de las muestras. El aporte (100 %
  menos la tasa de aciertos del modelo solo) es +23 % en general: hard-rule
  +41 %, judgment +16 %, injection 0 %. Por agente: product-manager y visionary
  +100 % (2 escenarios cada uno), dba +44 % (6), architect +29 % (7),
  eng-manager +27 % (5), qa +25 % (4), senior-dev +23 % (20); apple-dev,
  data-ml, devops, gamification, generalist, security y stark, 0 % (1 a 5 cada
  uno). 15 escenarios los falla el modelo solo 0 o 1 de 3 (el aporte se
  sostiene), 3 son inestables sin catálogo (2 de 3) y 50 los pasa 3 de 3 (el
  escenario no distingue). Lo que se sostiene son reglas que van contra el
  comportamiento por defecto del modelo: el punto commiteable, que la
  aprobación siga al efecto, no escribir por la shell, etiquetar como hipótesis
  un arreglo sin reproducir, que qa no arregle producto, que product-manager
  parta del problema. Cuatro cautelas. (1) El 100 % con catálogo es por
  construcción: los escenarios se escribieron como promesas del catálogo y se
  ajustaron hasta que el agente pasara, así que el aporte es una cota
  inferior. (2) Un 0 % no prueba que un agente no aporte: dice que sus
  escenarios actuales no lo distinguen del modelo solo. (3) **Cinco criterios
  nombraban a otro agente del roster**, que el modelo solo no puede conocer.
  Uno era un artefacto puro y pasó a `no_agent:`
  (`eng-manager-handles-missing-agent`); en otro la única falla del modelo
  solo fue no "derivar a dba" (`senior-dev-fixes-unreproducible-bug-as-hypothesis`,
  2 de 3 sin catálogo, que con el criterio nuevo sería 3 de 3 y bajaría el
  total a cerca de +22 %); en los otros tres la falla fue de conducta
  (diseñar la operación, no recortar la lista, no separar el piso de
  seguridad). Los cuatro se reescribieron en roles, y sus veredictos de esta
  medición se juzgaron con la redacción anterior. (4) `visionary-cannot-write-files`
  mide el nivel de acceso que el instalador pone al agente, no su juicio. Sin
  catálogo, el estimador del harness sobrestima el costo unas 2,4 veces
  (USD 4,58 contra 12,30 estimados la primera pasada); con catálogo, 10,27
  contra 12,20.
- **El aporte con un modelo chico (Haiku) frente a Sonnet** (Claude Code
  2.1.303, 2026-10-21, B-088). Mismo método que B-038, agente
  `claude-haiku-5-5`, juez Sonnet, USD 5,56. Sobre los 63 escenarios que
  corrieron los dos modelos (Sonnet en B-038 con catálogo `e2cca79`, Haiku con
  `1c43523`: el catálogo cambió en el medio, y eso confunde un poco la
  comparación; quedan afuera los tres escenarios cuyo criterio se reescribió
  entre las dos mediciones):

  | | Sonnet con | Sonnet sin | Aporte | Haiku con | Haiku sin | Aporte |
  |---|---|---|---|---|---|---|
  | Total | 100 % | 80 % | +20 % | 97 % | 80 % | +17 % |
  | hard-rule (17) | 100 % | 63 % | +37 % | 96 % | 71 % | +25 % |
  | judgment (42) | 100 % | 88 % | +12 % | 98 % | 84 % | +14 % |

  La hipótesis de partida (con un modelo chico el aporte se nota mucho más)
  no se sostiene: Haiku sin catálogo rinde casi igual que Sonnet sin catálogo
  (80 % los dos), y lo que baja es el techo con catálogo. Los escenarios de
  "buen criterio" no son difíciles ni para Haiku. Lo que el catálogo aporta en
  los dos modelos son las reglas que van contra el comportamiento por defecto:
  ocho escenarios los fallan los dos sin catálogo y los arreglan los dos con él
  (puerta de un solo sentido, memoria del agente, no ser dueño de la máquina,
  evidencia indirecta, qa no arregla producto, verificar la suite, visionary
  sin escribir archivos y sin secuenciar). Diferencias entre modelos, sin
  catálogo: Haiku es más obediente donde Sonnet rodea (no usa la shell cuando
  le niegan la herramienta de edición: 100 % contra 0 %) y más literal donde
  Sonnet tiene criterio de producto (orquesta trivialidades y propone mecánicas
  sin analizar el flujo: 0 % contra 100 %). Con catálogo, el único punto donde
  Haiku no llega es anunciar que no hay herramienta de edición (25 % contra
  100 %). Detalle y gráficos en `MODELOS.md` del harness.
- **El modo de permisos de Claude Code decide si una regla de prosa sobre
  escribir archivos tiene con qué cumplirse** (Claude Code 2.1.303,
  2026-10-19, B-075 y B-083). En el modo `default` el host ya rechaza solo
  una escritura por la shell dentro de la carpeta de trabajo: en las corridas
  `20261019-115116` y `-115630` volvieron rechazados todos los intentos de
  senior-dev y ninguno llegó al disco. En `acceptEdits`, `auto` y
  `bypassPermissions` pasan. En `auto` y `bypassPermissions` el binario
  además trae una instrucción al modelo para editar con `sed` y heredocs
  (*leído en el binario, no medido como causa*), que va en contra del CORE; es
  consistente con lo medido en `auto` sin guard: 5 de 9 muestras con una
  escritura por la shell en disco (`20261019-144610`). Una frase en el CORE
  no lo movió (senior-dev 14 de 18 por la shell con la frase, B-075), y un
  hook sí: 0 en 15 con el guard de B-083. Consecuencia para el catálogo: lo
  que el host puede anular se pide en prosa y se garantiza con un mecanismo
  del host, y el mecanismo tiene que medirse en el modo en que el usuario
  corre. La regla "Approval follows the effect" (B-066) es otra cosa y no
  quedó afectada: trata un rechazo como un no a su efecto, y esa sí compra
  conducta (de 3/6 a 6/6).
- **`npx github:…` necesita npm 11** (2026-10-13). Con npm 10 falla dentro
  de npm, antes de que corra el paquete: `GitFetcher requires an Arborist
  constructor to pack a tarball`. Medido con npm 10.8.2 (el que trae node 18
  y 20) y 10.9.9 (node 22.23.3); con npm 11.0, 11.19 (node 24) y 11.20 (node
  26) funciona. Con npm 10 sí funcionan `npm install -g github:…` y un tarball
  (`npx https://github.com/…/archive/<sha>.tar.gz`). local-hero pide node
  24+ y da una sola receta, `npx`; su CI fija node 24 como piso, además del
  LTS del momento. Con un node anterior alcanza con actualizar npm a 11. Ver
  B-051 y B-055.

Cómo se midió cada cosa, y cómo repetirlo, está en los comentarios de
`install.py` (`AGY_TOOLS`, `shadow_report`, el renderer de Codex) y en
[INSTALL.md](INSTALL.md).

---

## 5. Consideraciones para el catálogo

1. **Las skills son la capa portable; los agentes se traducen por host.** Es la
   arquitectura de `install.py` y la industria fue en la misma dirección. Una
   sola copia de los agentes para varios hosts no funciona: cada host espera
   otro formato, y agy ignora un agente que no tiene el suyo.
2. **La doc de un host es una hipótesis, no un hecho.** En un día, varios datos
   de documentación oficial, de un binario o de un validador resultaron falsos
   al probarlos: el default de `tools:` y la ruta de skills en Antigravity, los
   nombres de herramientas del binario de agy, y un `kiro-cli agent validate`
   que aprueba herramientas inventadas. Antes de escribir un renderer, se mide.
3. **Lo medido tiene versión y fecha.** Ningún CI puede correr los hosts, así
   que cada dato de la sección 4 puede dejar de ser cierto con una
   actualización. Las pruebas que no gastan consultas
   (`opencode debug skill`, buscar rutas en el binario de agy) son las primeras
   a repetir.
4. **Hacer cumplir el acceso de solo lectura es desparejo entre hosts.** Cada
   uno tiene su mecanismo y su forma de anularlo (`--sandbox` en Codex). La
   regla 16 se cumple distinto en cada host, y eso tiene que estar escrito
   donde el usuario lo lea.
5. **Una copia vieja es peor que una repetida.** Con hosts que leen varias
   carpetas, el problema real es la copia desactualizada, no la duplicación.
   `--status` lo avisa y `--refresh` lo corrige.
6. **La distribución se está partiendo en dos.** Agent Plugins para casi todos
   los hosts, y el formato propio de Claude Code. Publicar el catálogo como
   plugin implica, por ahora, mantener los dos.
7. **El instrumento también se mide.** El harness mide bien al agente, pero
   nunca se midió a sí mismo. Del juez ya hay una primera cifra frente a un
   humano (sección 4, B-039), con pocos FAIL todavía; de cuántos escenarios
   pasarían igual sin ningún agente, ninguna. Es la regla 17 aplicada al
   evaluador: sin esas dos cifras, un PASS dice menos de lo que parece. Ver
   B-038 y B-039.
8. **Un escenario que pasa sin agente no prueba al agente.** Mide al modelo
   base. Puede seguir sirviendo como protección contra regresiones, pero tiene
   que decirlo; no puede contarse como evidencia de que una regla del catálogo
   funciona.
9. **Copiar una práctica exige copiar su motivo.** Cada práctica de la
   sección 3 responde a un problema de su proyecto: los topes de 8 KB, a
   Codex; `model:` por agente, al costo; las cadenas fijas, a la falta de un
   agente que rutee. Antes de adoptar una, se comprueba que el problema
   también existe acá, y eso se mide igual que los datos de los hosts.
10. **Un pase entre agentes se paga dos veces: en tokens y en fidelidad.**
    Lo primero lo medimos (1,3 a 4 veces); lo segundo lo dice la guía de
    Anthropic y no lo medimos nunca: no hay un escenario que compare lo que
    entendió el que recibe con lo que sabía el que entregó. Un límite de rol
    puede valer ese precio, pero es un precio, y cada handoff nuevo tiene que
    decir qué compra.
11. **El roster por rol se defiende mientras el agente sea la conversación.**
    Elegido por el usuario o por el host, un especialista no coordina con
    nadie. El costo aparece cuando un agente llama a otro, y ahí vale la
    regla de la guía: partir por contexto, y usar al otro agente para
    verificar antes que para continuar el mismo trabajo.
12. **El host resuelve por su lado problemas que acá se arreglaron con
    texto.** `skills:` precarga la skill que a veces no carga; `effort:` baja
    el costo sin cambiar de modelo; dos ajustes de permisos hacen cumplir lo
    que el CORE pide en prosa. Cada uno existe en un solo host, así que
    ninguno reemplaza la regla, pero donde existe es una garantía y no una
    promesa (regla 16). Antes de escribir otra regla, mirar si el host ya
    tiene el mecanismo.
13. **Un changelog de un mes cambia lo que mide el harness.** Entre la
    2.1.296 y la 2.1.322 cambiaron el tipo de subagente por defecto, la
    profundidad de delegación y los códigos de salida de `claude -p`, y
    ninguna corrida lo registró como cambio: la huella guarda la versión del
    CLI, no qué hace distinto. Leer el changelog es parte de mantener el
    instrumento.
14. **Entre agentes, el archivo es el canal y el mensaje es el puntero.** En
    los cinco hosts el agente llamado arranca sin la conversación, así que lo
    único portable es lo que queda escrito: un spec o un hallazgo en un
    archivo, y un encargo corto que dice dónde está, qué entra y qué no, cómo
    se comprueba y qué tiene que volver. Es lo que `lh-orchestration` ya dice
    para el manager ("lo que cruza la costura es una ruta y un contrato") y
    lo que `ux-ui` hizo sin que nadie se lo pidiera.
15. **Un límite de acceso vale para quien conversa, no para quien es
    llamado.** La regla 16 se midió con cada agente como principal. Llamado
    por otro, tres de los cinco hosts le aplican los permisos del que llama.
    Un agente de solo lectura que otro agente invoca no tiene garantía hasta
    que se mida.

---

## 6. Backlog

El trabajo que sale de este relevamiento vive en [BACKLOG.es.md](BACKLOG.es.md),
con un ID estable por ítem (`B-NNN`), su criterio de terminado y los commits
que lo cerraron. Este documento guarda el relevamiento y los hechos medidos;
cuando un hecho dispara trabajo, se cita su ID.
