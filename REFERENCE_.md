# Guía rápida del catálogo (español)

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

```bash
./install.py --list                          # qué hay en el catálogo
./install.py --status                        # qué tenés instalado y si está al día
./install.py --all --tool claude --dry-run   # previsualizar
./install.py --all --tool claude             # instalar toda la suite
```

Herramientas: `claude`, `opencode`, `kiro`, `codex`, `shared`.

- **Instalá todo junto.** Los agentes se referencian entre sí; instalando uno
  suelto, sus handoffs apuntan a agentes que no están.
- **Para un equipo**: `--project ~/code/repo` deja la config dentro del repo
  (`.claude/`, `.opencode/`, …) y viaja con el código. Commiteala.
- **Codex** no tiene agentes con nombre: el instalador copia los cuerpos y
  escribe un roster en su `AGENTS.md`, respetando lo que ya tengas ahí.
- Cada instalación estampa de qué commit del catálogo salió, así `--status` te
  dice cuántos commits atrás estás y qué cambió.

El detalle completo, en [INSTALL.md](INSTALL.md).

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

---

## Si vas a agregar o editar algo

1. **Leé las reglas** en [AGENTS.md](AGENTS.md) — son 13 y cada una dice su
   porqué. Las que más se olvidan: la identidad de un agente no nombra
   tecnología (eso va en skills), y las skills externas se referencian por
   NOMBRE, nunca por ruta.
2. **Corré `./validate.py`** antes de commitear. Si tocaste agentes o skills,
   `./validate.py --write` regenera `GRAPH.md`.
3. **Esta guía solo cambia si agregás o sacás un agente.** El resto vive en los
   archivos de cada uno, que es donde se mantiene solo. Hay un check que
   verifica que la tabla de arriba tenga a los 15.
