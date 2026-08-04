# Cómo usar `install.py`

Instalador para copiar un agente (con sus skills) o skills sueltas hacia la
config **global** de una herramienta (Claude Code, opencode, Kiro CLI, Codex, o
la carpeta compartida `~/.agents`).

Automatiza el "Patrón B" de [INTEGRATION.md](INTEGRATION.md): en vez de que la
config de la herramienta REFERENCIE el catálogo, COPIA el agente + skills a los
directorios propios de la herramienta, así viajan con la máquina.

> Requisitos: Python 3.9+ (solo stdlib, cero dependencias externas).

---

## Atajo: instalar TODA la suite

Como el catálogo es una suite donde los agentes se referencian entre sí
(handoffs, skills cruzadas, orquestación), lo más común es instalar **todo
junto** — así se garantiza que todas las interacciones resuelven:

```bash
./install.py --all --tool claude            # previsualizá con --dry-run primero
```

Instala los 15 agentes (cada uno con su herencia incrustada) + las 48 skills,
cada skill una sola vez. Es el modo recomendado para dejar la oficina completa
en una herramienta.

---

## El flujo de tres pasos (siempre el mismo)

**El hábito de oro: `--list` → `--dry-run` → instalar.** Nunca instales a
ciegas: mirás qué hay, previsualizás, y recién ahí escribís.

### Paso 1 — Mirá qué hay

```bash
cd ~/Developer/local-agents
./install.py --list
```

Muestra los agentes con sus skills, y abajo las herramientas. Un
`[available, agents+skills]` significa que el script encontró la config de esa
herramienta y está lista para recibir. `[not detected]` = la herramienta no
está instalada (podés instalar igual, te va a preguntar).

### Paso 2 — Previsualizá con `--dry-run`

`--dry-run` muestra EXACTAMENTE qué archivos escribiría, sin tocar nada:

```bash
./install.py --agent architect --tool claude --dry-run
```

Salida de ejemplo:

```
  Installing agent 'architect' → Claude Code
    skill  → /Users/you/.claude/skills/design-review
    skill  → /Users/you/.claude/skills/mentoring
    skill  → /Users/you/.claude/skills/tradeoffs
    agent  → /Users/you/.claude/agents/architect.md
```

### Paso 3 — Instalá de verdad (sacás el `--dry-run`)

```bash
./install.py --agent architect --tool claude
```

El agente queda en `~/.claude/agents/architect.md` (con el frontmatter
`name`/`description` que Claude necesita, generado automáticamente) y sus skills
en `~/.claude/skills/`. Claude las descubre solas por su `description`.

---

## Modo interactivo (menús guiados)

Si no querés acordarte de los flags, corré el script pelado:

```bash
./install.py
```

Te pregunta con menús: ¿toda la suite / un agente / una skill suelta? → ¿cuál? →
¿qué herramienta? → y si algo ya existe, te da a elegir sobreescribir /
renombrar / saltear.

---

## Rutas no estándar (multi-cuenta, contenedores, CI)

Dos de las cinco herramientas publican una variable para mover su directorio de
config, y el instalador las respeta:

| Herramienta | Variable | Default |
|---|---|---|
| Claude Code | `CLAUDE_CONFIG_DIR` | `~/.claude` |
| Codex | `CODEX_HOME` | `~/.codex` |

```bash
CLAUDE_CONFIG_DIR=~/.claude-trabajo ./install.py --all --tool claude
```

Sirve para el caso típico de dos cuentas (personal y trabajo) y para
contenedores o CI donde el `HOME` no es el tuyo. `--status` respeta las mismas
variables, así que reporta el directorio que estés usando.

Las otras tres **no** tienen override y es a propósito: opencode documenta un
`~/.config/opencode` literal y **no lee `XDG_CONFIG_HOME`** (no lo "arregles"
para que lo lea, rompe); Kiro no publica ninguna variable; y `~/.agents` es
convención de este catálogo.

---

## Instalar en un proyecto (para compartir con el equipo)

Por defecto todo va a tu config global (`~/`). Con `--project` va **dentro del
repo**, así la config viaja con el código: tu compañero clona y ya la tiene, y
en CI también existe.

```bash
./install.py --all --tool claude --project ~/code/mi-repo
./install.py --all --tool claude --project          # sin ruta = directorio actual
```

Dónde aterriza cada herramienta:

| Herramienta | Global | Proyecto |
|---|---|---|
| Claude Code | `~/.claude/` | `.claude/agents/` y `.claude/skills/` |
| opencode | `~/.config/opencode/` | `.opencode/agents/` y `.opencode/skills/` |
| Kiro CLI | `~/.kiro/` | `.kiro/agents/` y `.kiro/skills/` |
| Codex | `~/.codex/` | `.codex/` **+ el roster en el `AGENTS.md` de la RAÍZ** |

Codex es el caso especial: por proyecto lee el `AGENTS.md` de la raíz del repo,
no uno adentro de `.codex/`. El roster se escribe ahí, entre marcadores — todo
lo que el equipo ya tenga en ese archivo se preserva.

**El de proyecto pisa al global** si comparten nombre, así que un repo puede
tener su propia versión de un agente sin afectar tu setup personal.

Dos guardarraíles: se niega a instalar sobre el catálogo mismo, y falla si la
ruta no existe.

> **Commiteá lo instalado.** El punto de `--project` es que viaje con el repo;
> si lo ignorás en `.gitignore` no compartís nada. Y `--status --project`
> te dice si lo commiteado sigue al día con el catálogo.

---

## Qué le pasa al agente al instalarse

La copia instalada no es idéntica al archivo del catálogo, y las dos diferencias
son deliberadas:

1. **La herencia se incrusta.** El `CORE.md` del padre entra en el cuerpo, así el
   agente copiado es autocontenido (ver más abajo).
2. **Las rutas a skills se convierten en NOMBRES.** En el catálogo, la tabla de
   skills enlaza a `skills/{nombre}/SKILL.md` y eso es navegable. Instalado, el
   agente es un archivo plano y las skills viven en un directorio hermano, así
   que esa ruta relativa no resuelve a nada.

Lo segundo salió de una traza real: un agente buscó sus propias skills, no las
encontró, y respondió *"no pude leer los skills de mi catálogo — voy con criterio
propio"*. **Trabajó sin ellas.** La alternativa —reescribir las rutas al layout
de cada herramienta— se descartó: son cinco destinos con cinco layouts, y todos
los hosts ya descubren skills **por nombre** desde su description. Un nombre
funciona en los cinco; una ruta funciona en uno.

El agente igual termina sabiendo dónde están: las **busca** en runtime y las
encuentra donde su host las ponga. La diferencia es que ahora lo averigua en vez
de creerle a una ruta que solo era cierta en la máquina donde se escribió.

Efecto colateral: la columna "File" de la tabla de skills desaparece en la copia
instalada, porque sin ruta solo repetía el nombre bajo un encabezado que mentía.

---

## ¿De qué versión del catálogo salió lo instalado?

Al instalar, el script deja un `.local-agents.json` en la config de la
herramienta con el commit del catálogo del que copió. `--status` lo lee y le
pregunta a git el resto:

```
Claude Code  (claude)
  /Users/you/.claude
    skills   48/48 from catalog
    agents   15/15 from catalog
    installed from 0035df7 — 2 commit(s) behind ed7c442
      skills changed: mockups, tradeoffs, verification
      agents changed: qa
```

No hay números de versión que mantener a mano: **la historia de git es el
changelog**. El manifiesto solo guarda de dónde salió la copia; el diff se
calcula al momento.

Degrada con honestidad en vez de inventar un número:

| Situación | Qué dice |
|---|---|
| Instalado antes de que existiera el estampado | `provenance: unknown` |
| Instalaste con cambios sin commitear | `installed from abc1234 + uncommitted changes` |
| Ese commit ya no está en la historia (rebase, otro clone) | `that commit is not in this history; reinstall to resync` |
| El catálogo no es un checkout de git (zip) | `catalog is not a git checkout here` — instala igual |

Con `--project`, el manifiesto queda dentro del repo. **Commitealo**: le dice al
equipo de qué commit del catálogo salió lo que están usando.

---

## ¿Qué tengo instalado y está al día?

`--list` te dice qué PODÉS instalar; `--status` te dice qué HAY instalado:

```bash
./install.py --status
```

```
Claude Code  (claude)
  /Users/you/.claude
    skills   48/48 from catalog · 14 foreign (untouched)
    agents   15/15 from catalog

Codex  (codex)
  /Users/you/.codex
    skills   48/48 from catalog · 1 foreign (untouched)
    agents   15/15 from catalog
      roster: 15 rows in AGENTS.md
```

Qué significa cada cosa:

| Etiqueta | Qué es |
|---|---|
| `N/M from catalog` | Cuántas de las del catálogo están presentes |
| `stale` | Está instalada pero **difiere** del catálogo — te falta reinstalar |
| `missing` | Está en el catálogo y no en la herramienta |
| `foreign (untouched)` | Tuya, ajena al catálogo. El instalador nunca la toca |
| `roster: N rows` | Sólo Codex y shared: filas en su `AGENTS.md`. Si el número no coincide con los cuerpos, te avisa |

`stale` no se calcula por fecha sino por **contenido**: las skills se comparan byte a byte y los agentes se vuelven a renderizar por el mismo camino que usa la instalación, así que un "al día" es exacto.

---

## Recetario de comandos

| Qué querés | Comando |
|-----------|---------|
| Ver todo lo disponible | `./install.py --list` |
| **Ver qué hay instalado y si está al día** | `./install.py --status` |
| **Instalar dentro de un repo (para el equipo)** | `./install.py --all --tool claude --project ~/code/repo` |
| Previsualizar (no escribe nada) | agregá `--dry-run` a cualquier comando |
| **Instalar toda la suite** | `./install.py --all --tool claude` |
| Instalar un agente + sus skills + herencia | `./install.py --agent architect --tool claude` |
| Un agente SIN sus dependencias | `./install.py --agent architect --tool claude --no-deps` |
| Instalar una skill sola | `./install.py --skill architect:tradeoffs --tool claude` |
| Varios agentes de una | `./install.py --agent qa --agent security --tool claude` |
| Menús guiados | `./install.py` |

El formato de skill suelta es `agente:skill` (corré `--list` si no te acordás el
nombre). También podés escribir solo el nombre de la skill si es único.

---

## Dependencias y herencia (importante)

Cuando instalás un agente, el script **también instala lo que ese agente
necesita para funcionar bien**, porque copiar rompe el árbol de referencias del
catálogo. Concretamente:

- **Skills cruzadas**: si un agente referencia skills de otros (ej. el
  `remediation` del security usa el `bug-reporting` del qa), esas skills se
  instalan también. Claude las descubre por su `description`.
- **Herencia incrustada (inlined)**: casi todos los agentes heredan el
  razonamiento del `generalist`, y los "peers" adoptan el Peer Contract del
  `senior-dev`. Como instalar el padre como agente separado NO le inyecta su
  razonamiento al hijo en runtime, el script **incrusta** la esencia del padre
  dentro del prompt del agente instalado (sección "Inherited context"). Usa el
  archivo **`CORE.md`** del padre — una versión curada y condensada de sus
  reglas siempre-encendidas, no un volcado del archivo entero. Si un padre no
  tiene `CORE.md`, cae al cuerpo completo. Así el agente copiado es
  autocontenido y liviano.

Si querés instalar SOLO el agente y sus skills propias, sin las dependencias:

```bash
./install.py --agent architect --tool claude --no-deps
```

> Con `--all` todo esto ya está cubierto: todos los agentes y skills quedan
> presentes, así que además de la herencia incrustada, los handoffs y la
> orquestación entre agentes también resuelven.

---

## Cuando algo ya existe (colisiones y renombrado)

El flag `--on-conflict` decide qué pasa si el agente/skill ya está instalado:

```bash
./install.py --agent architect --tool claude --on-conflict rename
```

| Valor | Comportamiento |
|-------|----------------|
| `ask` (default en interactivo) | Te pregunta por cada colisión |
| `rename` | Le pone `-2`, `-3`… automáticamente. **Reescribe el `name:` dentro del `SKILL.md`** para que coincida con la carpeta nueva (si no, la herramienta se confunde) |
| `overwrite` | Pisa lo que había |
| `skip` | Lo deja como estaba |

En modo interactivo, ante un choque te ofrece renombrar y elegís el nombre nuevo
a mano.

---

## Dónde aterriza cada cosa (por herramienta)

| Herramienta | Agentes | Skills |
|---|---|---|
| Claude Code (`claude`) | `~/.claude/agents/{nombre}.md` | `~/.claude/skills/{nombre}/` |
| opencode (`opencode`) | `~/.config/opencode/agents/{nombre}.md` | `~/.config/opencode/skills/{nombre}/` |
| Kiro CLI (`kiro`) | `~/.kiro/agents/{nombre}.json` | `~/.kiro/skills/{nombre}/` |
| Codex (`codex`) | `~/.codex/agents/{nombre}.md` + roster en `~/.codex/AGENTS.md` | `~/.codex/skills/{nombre}/` |
| Shared (`shared`) | `~/.agents/agents/{nombre}.md` + roster en `~/.agents/AGENTS.md` | `~/.agents/skills/{nombre}/` (lo leen opencode + Codex) |

**Nota sobre Codex:** no tiene concepto de "agente con nombre", así que el
script resuelve el hueco en dos partes: copia los cuerpos a
`~/.codex/agents/{nombre}.md` y escribe un **roster** (una tabla de una línea por
agente) dentro de `~/.codex/AGENTS.md`, que Codex carga solo. El modelo ve el
roster siempre y abre el cuerpo del agente que corresponde. Inlinear los 15
cuerpos serían ~110 KB en contexto en cada sesión; el roster son ~3 KB.

El roster va entre marcadores `<!-- BEGIN:local-agents -->` / `<!-- END: -->`:
todo lo que tengas fuera de ellos se preserva tal cual, y reinstalar reemplaza
el bloque en vez de duplicarlo. La tabla lista todos los agentes que haya en
`agents/`, no solo los de esa corrida — instalar uno suelto no borra los otros.

**Nota sobre `shared`:** `~/.agents/skills/` es una ubicación que leen tanto
opencode como Codex — instalás una vez, la ven las dos.

---

## Opciones útiles

| Flag | Para qué |
|------|----------|
| `--all` | Instalar toda la suite (15 agentes + 48 skills) |
| `--no-deps` | Instalar solo las skills propias del agente, sin herencia ni skills cruzadas |
| `--dry-run` | Muestra qué haría, no escribe nada |
| `--catalog PATH` | Usar otro catálogo (default: la carpeta donde vive el script) |
| `--on-conflict {ask,overwrite,rename,skip}` | Política ante colisiones |
| `--list` | Listar el catálogo y las herramientas detectadas, y salir |
| `--project [RUTA]` | Instalar dentro de un repo en vez de tu home (sin ruta = directorio actual) |
| `--status` | Listar lo que está INSTALADO en cada herramienta y si sigue al día, y salir |

---

## Cómo agregar una herramienta nueva

El registro de herramientas es data, no lógica enterrada. Abrí `install.py`,
buscá el bloque `TOOLS = [...]` y agregá un `Tool(...)`:

```python
Tool("mitool", "Mi Herramienta",
     HOME / ".mitool",             # dir cuya existencia = herramienta instalada
     HOME / ".mitool/skills",      # dónde van las skills
     HOME / ".mitool/agents",      # dónde van los agentes (None si no soporta)
     "claude_md"),                 # formato de archivo de agente
```

Con eso alcanza **si la herramienta usa un formato ya conocido**
(`claude_md`, `opencode_md`, `kiro_json`). Si necesita un formato de archivo de
agente NUEVO, agregá también una rama en la función `render_agent()`. Todo está
comentado en el script.
