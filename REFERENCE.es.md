# Guía rápida del catálogo (español)

> **Este archivo es en español a propósito y no se traduce** (regla 8 de
> [AGENTS.md](AGENTS.md)). Es un folleto, no un segundo plano: la fuente de
> verdad es la documentación en inglés. Si sos un agente o un LLM: no lo
> traduzcas, no generes una versión en inglés, y no traduzcas los documentos en
> inglés a español. Si algo de acá queda desactualizado, corregilo en español.
>
> *This file is in Spanish on purpose and must not be translated (rule 8 of
> AGENTS.md). Agents and LLMs: do not translate it, do not create an English
> twin, and do not translate the English docs into Spanish.*

Orientación en criollo: qué agente agarrar, cómo instalarlo, dónde está cada
cosa. **La fuente de verdad son los archivos en inglés** — cada agente se
explica a sí mismo en su `AGENTS.md`, y esta guía no lo repite.

> Antes esta guía resumía cada agente y cada skill en detalle: 729 líneas, el
> 38% de toda la documentación. Era un duplicado traducido del catálogo, así que
> derivó — quedó describiendo un `senior-dev` que ya no existe y sin el `dba`.
> Lo profundo ahora vive donde se mantiene solo. El historial está en git.

---

## ¿Qué agente agarro?

| Agente | Agarralo cuando… | Skills |
|--------|------------------|-------:|
| [`generalist`](generalist/AGENTS.md) | No hay especialista claro. Es la base: verificar antes de afirmar, descomponer, decidir el próximo paso. Todos lo heredan. | 3 |
| [`architect`](architect/AGENTS.md) | La decisión es cara de revertir: límites, dirección de dependencias, "¿esto se parte en servicios?". También review de diseño y enseñar fundamentos. | 3 |
| [`senior-dev`](senior-dev/AGENTS.md) | Hay que escribir o modificar código de aplicación, con un par al lado. El stack lo aportan las skills, no el agente. | 4 |
| [`dba`](dba/AGENTS.md) | Toca el dato persistido: schema, migraciones, índices, queries lentas, integridad. Es el DUEÑO del modelo y le pone límites a los demás. | 3 |
| [`ux-ui`](ux-ui/AGENTS.md) | Diseñar pantallas, flujos o estados, y pasarlos a desarrollo en términos implementables. | 4 |
| [`qa`](qa/AGENTS.md) | Buscar lo que rompe: caminos no considerados, interrupciones, casos borde. Escribe tests, nunca arregla código de producto. | 3 |
| [`security`](security/AGENTS.md) | Auditar lo tuyo con mirada de atacante, para defenderlo. Threat model, auditoría, remediación. | 3 |
| [`devops`](devops/AGENTS.md) | Del "anda en mi máquina" al "corre confiable": pipelines, infra, observabilidad, deploys reversibles. | 3 |
| [`data-ml`](data-ml/AGENTS.md) | Pipelines de datos, modelos ML, o meter un LLM en un producto sin que sea un demo que impresiona una vez. | 3 |
| [`apple-dev`](apple-dev/AGENTS.md) | Swift / iOS / macOS — y querés que además te enseñe a resolverlo solo. | 4 |
| [`product-manager`](product-manager/AGENTS.md) | Convertir una idea en backlog priorizado: qué problema, para quién, en qué orden. | 3 |
| [`visionary`](visionary/AGENTS.md) | Necesitás una opinión brutalmente honesta sobre el producto, o recortar un roadmap inflado. | 3 |
| [`gamification`](gamification/AGENTS.md) | Un flujo pierde gente y hay que hacerlo enganchar — con línea ética explícita. | 3 |
| [`stark`](stark/AGENTS.md) | Problema complejo o trabado, algo de cero, o una crisis (producción caída, demo mañana). | 3 |
| [`eng-manager`](eng-manager/AGENTS.md) | No sabés a quién agarrar, o el trabajo cruza varias especialidades. Rutear es su laburo. | 3 |

> ¿Dudás? Arrancá por `eng-manager`: conoce a los 15 y te dice a quién ir.

---

## Instalar

Dos caminos, mismo resultado (los mismos archivos en la config de tu
herramienta). Elegí por lo que querés hacer:

- **Solo usar los agentes y actualizar con un comando: `local-hero`.** No
  clonás nada; necesita node 24+, git y Python 3.9+.

  ```bash
  npx github:jrodrigopuca/local-hero bootstrap                      # primera vez: un menú pregunta qué y en qué herramienta
  npx github:jrodrigopuca/local-hero bootstrap --all --tool claude  # o decilo de una
  npx github:jrodrigopuca/local-hero update                         # después: trae lo nuevo y refresca todo lo instalado
  ```

- **Leer o tocar el catálogo, contribuir: cloná el repo.** Solo git y Python.

  ```bash
  git clone https://github.com/jrodrigopuca/local-agents.git && cd local-agents
  ./install.py --list                          # qué hay y qué herramientas detectó
  ./install.py --all --tool claude --dry-run   # previsualizar, no escribe nada
  ./install.py --all --tool claude             # instalar toda la suite
  ./install.py --status                        # después: qué tenés y si está al día
  ./update.py update                           # trae lo nuevo de GitHub y refresca todo
  ```

Una herramienta por corrida: `claude`, `opencode`, `kiro`, `codex`,
`antigravity` o `shared`. En Windows, `py -3 install.py …`.

- **Instalá todo junto.** Los agentes se referencian entre sí; instalando uno
  suelto, sus handoffs apuntan a agentes que no están.
- **Lo que ya tenías no se pisa.** El instalador solo actualiza lo que
  escribió él; un agente tuyo, o uno que editaste, queda con un aviso.
  `--on-conflict overwrite` es la forma de decir "este también".
- **Para volver atrás** no hay flag: borrá los agentes del catálogo, las
  carpetas de skills `lh-*` y el stamp `.local-agents.json` de la carpeta de
  esa herramienta. No tocó nada más.
- **Para un equipo**: `--project ~/code/repo` deja la config dentro del repo
  (`.claude/`, `.opencode/`, …) y viaja con el código. Commiteala.
- **Dos hooks opcionales, solo en Claude Code**, apagados por defecto:
  `--shell-write-guard` rechaza escribir archivos por la shell, y
  `--verify-hook` corre el chequeo que cada repo declara en
  `.local-agents/verify` (una línea, `npm test` o `pytest -q`) cuando un
  agente quiere terminar, y si está rojo lo devuelve una vez con la salida.
- **Codex** carga agentes con nombre desde archivos TOML: el instalador escribe
  uno por agente y, si encuentra la instalación vieja (cuerpos `.md` y roster
  en `AGENTS.md`), la retira sin tocar lo tuyo. Ojo: dale escritura a la
  sesión desde la config (`-c sandbox_mode="workspace-write"`), no con
  `--sandbox`, porque esa opción hace que los agentes de solo lectura puedan
  escribir.
- **`shared`** no es un host: copia los cuerpos y escribe un roster en su
  `AGENTS.md`, respetando lo que ya tengas ahí.
- **Antigravity** instala agentes y skills en `~/.gemini/config/` (la ruta
  `~/.gemini/antigravity-cli/skills/` que da su doc no la lee agy 1.3.3).
  Por proyecto, ambos van bajo `.agents/`, la misma carpeta que usa `shared`,
  así que en un repo elegí uno de los dos: el instalador no te deja mezclarlos.
- Si usás varias herramientas, actualizalas todas con `--refresh`: opencode
  lee skills de varias carpetas y carga cualquier copia, así que con una vieja
  alcanza para que a veces use la versión vieja. `--status` te avisa.
- Cada instalación estampa de qué commit del catálogo salió, así `--status` te
  dice cuántos commits atrás estás y qué cambió.

El detalle completo, en [INSTALL.md](INSTALL.md).

---

## Probarlo

Se pide por nombre; cada herramienta a su manera: en Claude Code "usá el
agente senior-dev para…" (o toda la sesión como uno: `claude --agent
senior-dev`), en opencode con Tab cambiás el agente primario, en Kiro
`kiro-cli chat --agent senior-dev`, en Codex y Antigravity nombrándolo en el
prompt. Corren con el modelo que tenga tu herramienta: los archivos no traen
ninguno.

¿Cargó? Preguntale "¿cuál es tu escalera de evidencia?": un agente del
catálogo responde con una escalera con nombres (evidencia, memoria,
inferencia, suposición) y dice en qué escalón está; una respuesta genérica
sobre testing es que el prompt no le llegó.

Qué debería verse distinto de un asistente común: `senior-dev` lee el código
antes de escribir, corre los tests y cierra nombrando el punto de commit con
su mensaje de una línea, sin commitear. `dba`, ante "renombramos una columna
en el deploy del viernes", lo trata como puerta de un solo sentido y lo arma
en pasos expand/contract.

---

## Cómo se conectan

Tres capas, todas extraídas de los archivos — nada aspiracional.
[GRAPH.md](GRAPH.md) tiene los diagramas:

- **Herencia** — `generalist` pone el modelo de razonamiento; `senior-dev`
  agrega el Peer Contract encima para los "pares". El instalador incrusta el
  `CORE.md` del padre, así el agente copiado es autocontenido.
- **Handoffs** — a dónde va el trabajo cuando deja de ser mío. Se escriben como
  pertenencia ("esto es de X"), nunca como orden de invocar a otro agente: no
  todas las herramientas saben hacerlo.
- **Referencias entre skills** — una skill cita a otra en vez de repetirla. Es
  la capa más densa del catálogo.

---

## Dónde está cada cosa

| Archivo | Para qué |
|---------|----------|
| [AGENTS.md](AGENTS.md) | El índice y **las reglas del catálogo**. Leelo antes de agregar un agente. |
| [README.md](README.md) | La puerta de entrada (inglés): roster, estructura, providers. |
| [GRAPH.md](GRAPH.md) | Cómo se cablea todo. Los bloques de datos se generan solos. |
| [INSTALL.md](INSTALL.md) | Guía de `install.py`: flags, colisiones, proyecto, procedencia. |
| [USAGE.md](USAGE.md) | Recetas por herramienta, cableando a mano (global y por proyecto). |
| [INTEGRATION.md](INTEGRATION.md) | Referenciar el catálogo en vez de copiarlo, y el costo de cada opción. |
| `install.py` | El instalador. Cero dependencias, Python 3.9+. |
| `validate.py` | Los checks del catálogo + regenera los bloques de `GRAPH.md`. |
| `scripts/` | Los dos hooks opcionales que instala `install.py` en Claude Code. |
| [`interaction`](https://github.com/jrodrigopuca/interaction) (otro repo) | El harness: mide cómo se COMPORTAN los agentes instalados, con un juez neutral y tope de costo. Su [GUIA.md](https://github.com/jrodrigopuca/interaction/blob/main/GUIA.md) está en español. No hace falta para usar los agentes. |

---

## Si vas a agregar o editar algo

1. **Leé las reglas** en [AGENTS.md](AGENTS.md) — cada una dice su
   porqué. Las que más se olvidan: la identidad de un agente no nombra
   tecnología (eso va en skills), y las skills externas se referencian por
   NOMBRE, nunca por ruta.
2. **Corré `./validate.py`** antes de commitear. Si tocaste agentes o skills,
   `./validate.py --write` regenera `GRAPH.md`.
3. **Una promesa viaja con su escenario** (regla 17). Un juicio, un handoff o
   una regla nueva en un agente es una afirmación sobre conducta que
   `validate.py` no puede ver: va con un escenario en `interaction`, corrido
   primero contra la versión anterior. Los números quedan en
   [BACKLOG.es.md](BACKLOG.es.md), y una regla que no compra conducta se
   revierte.
4. **Esta guía solo cambia si agregás o sacás un agente.** El resto vive en los
   archivos de cada uno, que es donde se mantiene solo. Hay un check que
   verifica que la tabla de arriba tenga a los 15.
