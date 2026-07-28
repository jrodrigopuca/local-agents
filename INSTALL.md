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

Instala los 14 agentes (cada uno con su herencia incrustada) + las 45 skills,
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

## Recetario de comandos

| Qué querés | Comando |
|-----------|---------|
| Ver todo lo disponible | `./install.py --list` |
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
| Codex (`codex`) | *(sin agentes con nombre)* | `~/.codex/skills/{nombre}/` |
| Shared (`shared`) | — | `~/.agents/skills/{nombre}/` (lo leen opencode + Codex) |

**Nota sobre Codex:** no tiene concepto de "agente con nombre". Si instalás un
agente a Codex, el script copia sus skills y te imprime la línea que tenés que
agregar a mano en tu `~/.codex/AGENTS.md`.

**Nota sobre `shared`:** `~/.agents/skills/` es una ubicación que leen tanto
opencode como Codex — instalás una vez, la ven las dos.

---

## Opciones útiles

| Flag | Para qué |
|------|----------|
| `--all` | Instalar toda la suite (14 agentes + 45 skills) |
| `--no-deps` | Instalar solo las skills propias del agente, sin herencia ni skills cruzadas |
| `--dry-run` | Muestra qué haría, no escribe nada |
| `--catalog PATH` | Usar otro catálogo (default: la carpeta donde vive el script) |
| `--on-conflict {ask,overwrite,rename,skip}` | Política ante colisiones |
| `--list` | Listar y salir |

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
