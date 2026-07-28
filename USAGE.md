# Guía de uso: el catálogo en cada herramienta

Cómo usar los agentes del catálogo en Claude Code, opencode, Kiro CLI y Codex —
de forma global (disponibles en todo lados) o por proyecto. Los principios
generales (referenciar, nunca copiar) están en
[INTEGRATION.md](INTEGRATION.md); esto son las recetas concretas por
herramienta, verificadas contra la documentación oficial (julio 2026).

> **Rutas en esta guía.** Los ejemplos usan `~/Developer/local-agents` (o
> `/Users/you/Developer/local-agents` donde la herramienta exige ruta absoluta).
> Reemplazalo por donde hayas clonado el catálogo. Las rutas absolutas a un home
> no existen en la máquina de un compañero ni en CI — ver la última sección.

## Resumen: el mecanismo de cada herramienta

| Herramienta | Mecanismo | Global | Por proyecto | ¿Referencia archivos? |
|---|---|---|---|---|
| Claude Code | Subagentes `.md` con frontmatter | `~/.claude/agents/` | `.claude/agents/` | Vía instrucción "Read X" en el body |
| opencode | Agentes `.md` con frontmatter, o JSON | `~/.config/opencode/agents/` | `.opencode/agents/` | Sí: `{file:...}` en el prompt del JSON |
| Kiro CLI | Agentes JSON | `~/.kiro/agents/` | `.kiro/agents/` | Sí, nativo: `"prompt": "file://..."` |
| Codex | AGENTS.md jerárquico + skills | `~/.codex/AGENTS.md` y `~/.codex/skills/` | `AGENTS.md` en la raíz del repo | Los AGENTS.md se concatenan solos |

Regla transversal: **el agente necesita permiso de lectura** para cargar su
definición y sus skills bajo demanda. Sin `read`, tenés un asistente genérico
con nombre lindo.

---

## Claude Code

### Global (disponible en todos los proyectos)

Crear `~/.claude/agents/architect.md`:

```markdown
---
name: architect
description: Senior Architect mentor - guidance on architecture, tradeoffs, design reviews, and learning paths. Helpful first, challenging when it matters.
---

Read /Users/you/Developer/local-agents/architect/AGENTS.md and fully adopt it:
identity, judgment model, and escalation ladder. It inherits
/Users/you/Developer/local-agents/generalist/AGENTS.md — read that too.
Load the skills it references when their triggers fire.
```

- El body del archivo es el system prompt del subagente; el frontmatter mínimo
  es `name` + `description` (la description decide cuándo Claude lo delega —
  escribila pensando en el trigger, no en el marketing).
- Opcional: `tools:` para restringir herramientas y `model:` para fijar modelo.
- Se invoca pidiéndolo ("usá el agente architect") o Claude lo delega solo
  cuando la tarea matchea la description.

### Por proyecto

Mismo archivo en `.claude/agents/architect.md` dentro del repo. El de proyecto
pisa al global si comparten nombre.

### Bonus: las skills del catálogo son compatibles directo

Los SKILL.md del catálogo siguen el spec de Agent Skills que Claude Code lee
nativamente. Para exponer una skill suelta sin pasar por el agente:

```bash
ln -s ~/Developer/local-agents/generalist/skills/verification ~/.claude/skills/verification
```

Ojo con colisiones de nombre con skills existentes; si chocan, renombrá el
symlink y el `name:` del frontmatter debe seguir matcheando la carpeta.

---

## opencode

### Global

Crear `~/.config/opencode/agents/architect.md` (el nombre del archivo = nombre
del agente):

```markdown
---
description: Senior Architect mentor - helpful first, challenging when it matters
mode: primary
---

Read /Users/you/Developer/local-agents/architect/AGENTS.md and fully adopt it:
identity, judgment model, and escalation ladder. It inherits
/Users/you/Developer/local-agents/generalist/AGENTS.md — read that too.
Load the skills it references when their triggers fire.
```

- `mode: primary` = seleccionable como agente principal (Tab);
  `mode: subagent` = solo delegable.
- Frontmatter soporta además `model`, `temperature` y `permission` (p. ej.
  `permission: { edit: deny }` para un agente de solo consulta).

### Alternativa JSON con `{file:}` — prompt directo sin instrucción de lectura

En `opencode.json` el prompt puede SER el archivo:

```json
"agent": {
  "architect": {
    "mode": "primary",
    "description": "Senior Architect mentor",
    "prompt": "{file:/Users/you/Developer/local-agents/architect/AGENTS.md}"
  }
}
```

Tradeoff: `{file:}` inyecta el contenido del AGENTS.md como system prompt (no
depende de que el modelo "lea bien"), pero NO resuelve la herencia — el
generalist no viene incluido. Para los agentes que heredan (architect,
senior-dev, ux-ui), la variante markdown con instrucción "read both" es más
fiel. Las rutas de `{file:}` se resuelven relativas al archivo de config.

### Por proyecto

Mismo markdown en `.opencode/agents/architect.md` del repo. Además, opencode
lee `AGENTS.md` en la raíz del proyecto como reglas generales — ahí podés
apuntar al catálogo para que TODO agente del proyecto conozca las convenciones.

---

## Kiro CLI

### Global

Crear `~/.kiro/agents/architect.json` (el nombre del archivo = nombre del
agente):

```json
{
  "name": "architect",
  "description": "Senior Architect mentor - helpful first, challenging when it matters",
  "prompt": "file:///Users/you/Developer/local-agents/architect/AGENTS.md",
  "resources": [
    "file:///Users/you/Developer/local-agents/generalist/AGENTS.md"
  ],
  "tools": ["read", "write", "shell"],
  "allowedTools": ["read"]
}
```

- `"prompt": "file://..."` es Patrón A nativo: rutas absolutas se usan tal
  cual, relativas se resuelven desde el directorio del config.
- `resources` precarga archivos como contexto — ideal para la herencia del
  generalist. Podés precargar también las skills con un glob
  (`"file:///Users/you/Developer/local-agents/architect/skills/**/*.md"`), pero eso
  rompe el disclosure progresivo: pagás todo el contexto siempre. Preferí
  precargar solo los AGENTS.md y dejar que las skills se lean bajo demanda con
  el tool `read`.

### Por proyecto

Mismo JSON en `.kiro/agents/architect.json` del repo (vale solo desde ese
directorio hacia abajo).

### Uso

```bash
kiro-cli agent list                    # verificar que aparece
kiro-cli chat --agent architect        # arrancar con el agente
```

---

## Codex

Codex no tiene "agentes con nombre": su mecanismo es la jerarquía de AGENTS.md
(se concatenan de la raíz hacia tu directorio; el más cercano manda) más skills.
Dos movimientos:

> Si lo que querés es la suite completa, `./install.py --all --tool codex` ya
> hace esto solo: copia los cuerpos a `~/.codex/agents/` y escribe el roster en
> `~/.codex/AGENTS.md` entre marcadores, sin tocar lo que tengas ahí. Lo de
> abajo es la receta a mano, para cablear un agente puntual referenciando el
> catálogo en vez de copiarlo.

### Global — el generalist como base de todo

En `~/.codex/AGENTS.md` (guía personal, aplica en todos lados):

```markdown
Adopt the reasoning model defined in
/Users/you/Developer/local-agents/generalist/AGENTS.md — operating loop, epistemic
rules, and reporting contract. Load the skills it references when their
triggers fire.
```

### Por proyecto — el rol que ese repo necesita

En el `AGENTS.md` de la raíz del repo:

```markdown
For this repository, additionally adopt
/Users/you/Developer/local-agents/senior-dev/AGENTS.md (work as a peer, not an
assistant).
```

Como los archivos se concatenan (global + proyecto), la herencia se arma sola:
generalist de base global, rol específico por repo.

### Skills — compatibles directo, igual que en Claude Code

Codex deprecó los custom prompts en favor de Agent Skills — el MISMO spec
SKILL.md del catálogo. Symlink y listo:

```bash
mkdir -p ~/.codex/skills
ln -s ~/Developer/local-agents/generalist/skills/verification ~/.codex/skills/verification
ln -s ~/Developer/local-agents/architect/skills/tradeoffs ~/.codex/skills/tradeoffs
```

Codex carga solo name+description de cada skill y trae el contenido cuando
matchea la tarea (disclosure progresivo nativo). Se invocan explícito con
`/skills` o `$nombre`, o implícito por description. Codex también escanea
`~/.agents/skills/` — ubicación pensada para compartirse entre herramientas;
si mañana otra CLI la adopta, un solo set de symlinks sirve para todas.

---

## ¿Global o por proyecto? El criterio

| Situación | Elegí |
|---|---|
| Tu forma de trabajar, siempre (generalist) | Global |
| Roles que usás en cualquier lado (architect, senior-dev, ux-ui) | Global |
| Un repo con equipo: convenciones que viajan con el código | Por proyecto (y commiteá la config) |
| Ojo: config por proyecto que referencia `~/Developer/local-agents` | Solo funciona en TU máquina — para equipos, vendorizá el catálogo en el repo o usá Patrón B |

Esa última fila es la trampa para tener presente: las rutas absolutas a tu home
no existen en la máquina de un compañero ni en CI.

## Smoke test: verificar que el agente cargó de verdad

Después de configurar, no asumas — verificá (peldaño 4, no peldaño 2). Abrí el
agente y preguntale algo que solo sabe si leyó el catálogo:

> "¿Cuál es tu escalera de evidencia y qué peldaño exige 'done'?"

Si responde los 4 peldaños (Observado > Testeado > Leído > Recordado) y "mínimo
el 3", cargó. Si te da una respuesta genérica sobre testing, el prompt no llegó
— revisá permisos de `read` y rutas.
