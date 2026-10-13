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
| Topes de tamaño | Archivos de contexto de ~150 líneas; cuerpo de skill de ~8 KB, el límite que le atribuyen a Codex; lo que sobra se parte en `references/` | Ninguno. `llm-integration` pesa 10.999 bytes (*medido*); ver B-042 |
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
| Evals de disparo con casi-aciertos | skill-creator | B-041, B-043 |
| Usar la herramienta oficial antes que construir | `claude plugin eval` | B-047 |
| Actualizar con un comando, sin gestionar el clon | `npx skills` | B-050, B-051 |
| Tope de costo por corrida | `claude plugin eval` | B-044 |
| Topes de tamaño por host | wshobson | B-042 |
| Humo con CLI reales en CI | wshobson | B-046 |
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
| **Codex 0.144.5** | TOML en `~/.codex/agents`, `.codex/agents` | `~/.codex/skills`; `~/.agents/skills` (documentado) | `sandbox_mode = "read-only"` | El flag `--sandbox` pisa el modo de cada agente; `-c sandbox_mode=...` y `config.toml` no. `codex exec` espera stdin si no se cierra |
| **Antigravity (agy 1.3.3)** | `~/.gemini/config/agents`, `.agents/agents`; con el mismo nombre **gana el del proyecto** | `~/.gemini/config/skills`, `.agents/skills` | allowlist `tools:` | La doc da `~/.gemini/antigravity-cli/skills/` para el CLI y **no se lee**. Sin `tools:` el agente recibe un set mínimo (sin escribir ni buscar). Un nombre de herramienta desconocido aborta el arranque. Un agente sin frontmatter se ignora: `--agent` usa el global de ese nombre si existe, o el agente principal, sin avisar |
| **Claude Code 2.1.296** | `~/.claude/agents`, `.claude/agents` | `~/.claude/skills`, `.claude/skills`. **No** lee `~/.agents/skills` ni `.agents/skills` | allowlist `tools:` | Se puede medir gratis: el evento `init` de `claude -p --output-format stream-json --verbose` lista las skills cargadas antes de consultar al modelo. El comportamiento de los agentes lo prueba el harness |
| **Kiro (kiro-cli 2.29.1)** | JSON en `~/.kiro/agents`, `.kiro/agents` | `~/.kiro/skills`, `.kiro/skills`, vía `resources` `skill://` (el `~` funciona también por proyecto) | lista `tools`, que se hace cumplir | **Lee solo la primera línea de la descripción de una skill**: con `description: >` la ve vacía, y la skill no se dispara nunca. `code` modifica archivos (AST rewrite) y `subagent` delega en un agente que escribe. `kiro-cli agent validate` acepta herramientas y campos inventados |

### Otros hallazgos medidos

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
   nunca se midió a sí mismo. No sabemos cuánto acierta el juez frente a un
   humano, ni cuántos escenarios pasarían igual sin ningún agente. Es la regla
   17 aplicada al evaluador: sin esas dos cifras, un PASS dice menos de lo que
   parece. Ver B-038 y B-039.
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
