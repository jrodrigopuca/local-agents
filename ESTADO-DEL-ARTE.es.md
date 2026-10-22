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
prácticas de evaluación (sección 3), el 2026-10-12. Próxima revisión: 2027-01,
o antes si un host cambia de versión mayor o aparece un estándar nuevo.**

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
| Tope de costo por corrida | `claude plugin eval` | B-044 |
| Humo con CLI reales en CI | wshobson | B-046 hecho para claude y opencode; kiro pide login |
| Escenarios bajo presión con excusas registradas | superpowers | B-045 |

**Lo que adoptamos sin código:**

- **Una descripción de skill lista disparadores, no el flujo** (superpowers:
  cuando la descripción resumía el proceso, el agente seguía el resumen y
  salteaba el cuerpo). La regla 14 ya pide que el disparador nombre un
  umbral; esto suma que la descripción no anticipe los pasos. Rige para toda
  descripción que se reescriba, y B-041 la aplica.

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

---

## 6. Backlog

El trabajo que sale de este relevamiento vive en [BACKLOG.es.md](BACKLOG.es.md),
con un ID estable por ítem (`B-NNN`), su criterio de terminado y los commits
que lo cerraron. Este documento guarda el relevamiento y los hechos medidos;
cuando un hecho dispara trabajo, se cita su ID.
