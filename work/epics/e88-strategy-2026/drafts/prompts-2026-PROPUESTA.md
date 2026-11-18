# Prompts del Workbook Strategy 2026 — propuesta (borrador)

Estado: borrador para que Eduardo lo revise. No se cambió ningún archivo del repo.

Fuente: Workbook Strategy 2026, 24 páginas. Revisé cada página citada.

## 0. Dos reglas del repo que mandan sobre esta propuesta

1. **La página no va dentro del prompt.**
   - El motor rechaza `ai_prompt.page` (prueba `test_ai_prompt_page_is_rejected`).
   - Varias pruebas exigen que `ai_prompt` tenga solo `text`.
   - Propuesta: la cita «Workbook Strategy 2026, p. N» va como comentario YAML encima del prompt.
     También va en un mapa de cobertura nuevo (ver sección D).
2. **Cada hoja muestra un solo prompt, y solo al final.**
   - Hoy el prompt sale en la revisión final y en la vista guardada.
   - Una hoja sin `guide` nunca muestra su prompt.

Palabras que no pueden salir en el texto público: «Scaling Up», «BHAG», «OPSP», «Rocks» y las demás de
`governance/public-boundary.yaml`. Por eso digo «meta grande» y quito «the Scaling Up way».

---

## B. El prompt de arranque («AI Setup», p. 4)

### Qué dice el workbook (p. 4)

Se pega una vez, al empezar. Abre un solo chat para todos los ejercicios del día.
La nota dice: «tenga a la mano su sitio y 2 competidores».

### Paráfrasis propuesta

> Estoy en un taller de estrategia. Vamos a hacer varios ejercicios en un solo chat. Usa todo lo
> que te diga; no me hagas repetir. Mi negocio:
> - Giro: [giro]
> - Ventas al año: ~$[monto] | Personas: [número]
> - Cómo gana dinero, en una oración: [modelo]
> - Mi sitio web: [URL] | Dos competidores: [URL], [URL]
> - Lo que quiero hoy: [una estrategia simple / algo que de verdad me haga distinto / una meta más grande]
>
> Lee mi sitio y los de mis competidores. Dime en 3 o 4 oraciones qué ves: para quién decimos que
> somos, qué prometemos y dónde sonamos igual que todos. Luego espera. Te voy a pegar un prompt por
> ejercicio. Usa lo que ya sabes. Si te falta algo, pregúntame; no adivines. Cuando te pida que me
> entrevistes, hazme una pregunta a la vez.

### Dónde vive: 3 opciones

| Opción | Qué cambia | Costo | Lo que ve el dueño |
|---|---|---|---|
| 1. Sin tocar el motor | El paso 1 de `swt.yaml` dice en su `how`: «Antes de empezar, pega el prompt de arranque en tu chat de IA». El texto vive en un archivo nuevo `conocimiento/strategy/ai-setup.yaml` y el skill `escala-worksheet` lo lee | Solo YAML y una línea en el skill | Lo ve solo si el skill lo lee bien; el motor no lo garantiza |
| 2. **Cambio chico al motor (recomendada)** | `ai_prompt` acepta una lista. Cada prompt tiene `text`, un `title` opcional y `at: start` o `at: end` | Una historia de unos 3 puntos | El prompt de arranque sale junto con el paso 1; el de cierre sale al final, como hoy |
| 3. Hoja aparte «Arranque con IA» | Una hoja nueva con 1 paso | Rompe la regla de 3 tips mínimos; no hay tips que citar | Una hoja que no se llena; confunde |

**Recomiendo la opción 2.** Además resuelve la sección C3, donde la hoja de resumen de visión trae 2 prompts.

**Dónde se pone:** en `swt.yaml`, como prompt `at: start`. Razones:
- SWT es el primer ejercicio de la agenda (p. 2).
- La p. 4 está justo antes de las páginas de SWT (p. 5 y 6).

### Esbozo del cambio al motor (opción 2)

```python
# coaching/worksheet/guide.py — HOY
class AiPrompt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: Text
...
    ai_prompt: AiPrompt | None = None

# PROPUESTA
class AiPrompt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: Text
    title: Text | None = None
    at: Literal["start", "end"] = "end"
...
    ai_prompt: AiPrompt | list[AiPrompt] | None = None
    # un solo objeto sigue siendo válido: ninguna hoja actual se rompe
```

- `__init__.py`: `_ai_prompt_text` devuelve los prompts `end` (con su título).
  `_step_lines` muestra los prompts `start` solo en el paso 1.
- `view.py`: `SheetView.ai_prompt` pasa de `str | None` a una lista de (título, texto).
  La vista HTML y la MD pintan un bloque por prompt.
- La página sigue fuera del prompt. `at` y `title` no son página.

Pruebas nuevas (TDD):
1. Un objeto solo sigue cargando igual (las 21 hojas actuales pasan sin cambios).
2. Una lista con `at: start` sale en el paso 1 y no en la revisión final.
3. Dos prompts `end` salen los dos en la vista, en orden, con su título.
4. `page` sigue rechazado dentro de cada prompt de la lista.

---

## C. Prompts 2026 por hoja

### C1. `swt.yaml` — Fortalezas, debilidades y tendencias (p. 5 y 6)

PRECAUCIÓN: hoy `swt.yaml` no tiene `guide`. Si solo le agrego `ai_prompt`, **nunca se muestra**.
Hay que pasarla a hoja guiada: pasos, mínimo 3 tips y vista.

Nota sobre las páginas: el prompt de SWT está solo en la p. 5. La p. 6 es la hoja impresa con las preguntas.

**Actual**

```yaml
# sin guide, sin ai_prompt
metadata:
  fields:
    - "Strengths: top 3-5 internal capabilities that differentiate us"
    - "Weaknesses: top 3-5 internal gaps that limit growth or create risk"
    - "Trends: top 3-5 external forces shaping industry (macro, competitive, tech)"
    - "Key insight: which trends amplify strengths? which expose weaknesses?"
    - "OPSP input: top 1-2 items per category for the OPSP bottom strip"
```

**Nuevo — prompt de cierre**

```yaml
# Workbook Strategy 2026, p. 5 (prompt «SWT»).
ai_prompt:
  text: "Haz un análisis de fortalezas, debilidades y tendencias de mi negocio. Las fortalezas y las debilidades son de adentro: dame 5 de cada una, pensando en competidores, equipo, dinero para crecer, base de clientes y distribución. Las tendencias son de afuera y ahí está el dinero de verdad: dame 12 que cubran mi industria, tecnología, mi región, el mundo, cultura, medios, política y educación, cada una con una señal real que la respalde. Ordénalas por qué tan fuerte nos pegarían en los próximos 3 años y marca si cada una es amenaza, oportunidad o las dos. Luego hazme 3 preguntas, una a la vez, sobre las tendencias que estoy ignorando porque actuar sobre ellas me resulta incómodo."
```

Cambio frente al original: quité «the Scaling Up way» (palabra prohibida en texto público).

**Nuevo — lista «Tendencias 2026/2027» (p. 5)**

Va en el `how` del paso `tendencias-2026`. Paráfrasis; lo que está entre paréntesis lo agregué yo para que se entienda.

1. Agentes de IA que hacen el trabajo, no solo el borrador.
2. ¿De quién es tu cara y tu voz? La pelea por la imagen en la música y el cine.
3. Los medicamentos GLP-1 (como Ozempic) cambian la comida, el alcohol y el comercio.
4. Vivir sano más años es el nuevo símbolo de estatus.
5. La gente tiene menos amigos y vuelven los «terceros lugares» (el café, el club, la plaza: ni casa ni trabajo).
6. Fuera celulares de las escuelas, y regresa lo análogo.
7. La baja de nacimientos llega a los consejos y a la política.
8. La «generación sándwich» (cuida a sus hijos y a sus papás a la vez) se aprieta por los dos lados.
9. Lo en vivo y en persona se cobra más caro.
10. La confianza pasa de las instituciones a las personas.

**Nuevo — esbozo de la guía** (los ejemplos los escribo en la historia, con «Tortillería El Sol:»)

| Paso | Pregunta | Fuente |
|---|---|---|
| `tendencias-2026` | ¿Cuáles de estas 10 tendencias tocan tu negocio? | p. 5, lista |
| `tendencias` | ¿Qué cambios de afuera pueden pegarle a tu industria? Revisa 15 temas: industria, tecnología, región, mundo, cultura, salud, medios, política, espiritualidad, moda, música y arte, tele y cine, humor, familia, educación | p. 5 y p. 6 |
| `fortalezas` | ¿Qué fuerzas tuyas explican tu éxito? Piensa en equipo, tecnología, rapidez para cambiar, ejecución y márgenes | p. 5 y p. 6 |
| `debilidades` | ¿Qué debilidades tuyas no van a cambiar pronto? Piensa en competidores, equipo, dinero para crecer, base de clientes y distribución | p. 5 y p. 6 |
| `ideas` | Cruza una tendencia con una fortaleza o una debilidad. ¿Qué idea sale? | p. 5, lámina de líneas «Idea» |

Vista propuesta: «Lo que pasa afuera» (tendencias-2026, tendencias) · «Lo que tienes adentro» (fortalezas, debilidades) · «Tus ideas» (ideas).

Tips: solo encontré **2 fuentes reales** en el repo que sirven aquí. Faltan uno o más.
- `work/research/e87-tips/sandbox.md#f4` (triangulado): escribir 3 a 5 cambios con una señal que se pueda medir. Sirve para `tendencias`.
- `work/research/e87-tips/differentiating-activities.md#f4` (triangulado): «buen servicio» no cuenta. Sirve para `fortalezas`.
- Falta el tercero. Hay que investigar SWT con `/rai-research` antes de pasar la hoja a guiada (la regla pide mínimo 3 tips).

Otros cambios que trae pasarla a guiada:
- `name_es` actual sin acentos: «Hoja de Trabajo de Analisis SWT». Propongo «Fortalezas, debilidades y tendencias».
- El `summary` está en inglés y dice «OPSP» (palabra prohibida en texto público). Hay que reescribirlo en español.
- `metadata.fields` se quita: la guía lo reemplaza.
- Si se aprueba la opción 2 de la sección B, aquí va también el prompt de arranque con `at: start`.

---

### C2. `differentiating-activities.yaml` — Actividades diferenciadoras (p. 7)

Solo cambia el prompt. Los pasos actuales ya siguen la hoja impresa de la p. 8
(competidores; personas, producto, operaciones, términos; de 3 a 5 actividades).

Nota sobre las páginas: el prompt está solo en la p. 7. La p. 8 es la hoja impresa.

**Actual (prompt 2025)**

```yaml
ai_prompt:
  text: "Con mi Cliente central, mi Promesa de marca y mis 2 o 3 competidores, propón 5 actividades en personas, producto, operaciones y términos que me hagan distinto. Explica cómo se refuerzan entre sí y qué tendría que dejar de hacer."
```

**Nuevo (prompt 2026)**

```yaml
# Workbook Strategy 2026, p. 7 (prompt «Differentiating Activities»).
ai_prompt:
  text: "Michael Porter dice que la estrategia es una posición única y valiosa que se construye con actividades distintas. Hazme 3 preguntas, una a la vez, sobre cómo entregamos de verdad: qué nota el cliente, qué nunca ve y dónde hacemos las cosas por el camino difícil a propósito. Luego compara mis respuestas con los sitios de mis competidores y nombra de 3 a 5 actividades que me podrían hacer distinto. Para cada una dime: ¿el cliente la ve?, ¿es difícil de copiar?, ¿refuerza a las demás? Tacha las que todos hacen aunque suenen bonito. Al final dime qué crea la combinación —la ventaja y la barrera para la competencia— y las 2 cosas que tendría que dejar de hacer para que sean reales."
```

Qué se pierde y qué se gana:
- Se pierde la mención directa a «Cliente central» y «Promesa de marca».
  Si se usa el chat continuo de la sección B, la IA ya los tiene.
- Se gana la entrevista de 3 preguntas, la comparación con los sitios y el filtro «difícil de copiar».

Pruebas: la de esta hoja solo pide que exista el texto. No hay que cambiar pruebas.

---

### C3. `vision-summary.yaml` — Resumen de visión (p. 20)

La p. 20 trae **2 prompts**:
- «Vision Summary»: todo el día en una sola hoja, más las contradicciones.
- «Make Change Stick»: 10 tareas semanales y un archivo de calendario.

**Actual**

```yaml
ai_prompt:
  text: "Con mi resumen de visión, mis prioridades del trimestre y mis números, escribe 10 tareas, una por semana, para las próximas 10 semanas. Que cada una me tome menos de una hora y casi no cueste dinero. Ponle dueño, fecha y cómo sabré que quedó hecha. Al final pregúntame a cuál me comprometo primero."
```

**Nuevo — con el cambio al motor (opción 2 de la sección B)**

```yaml
# Workbook Strategy 2026, p. 20 (prompts «Vision Summary» y «Make Change Stick»).
ai_prompt:
  - title: "Tu día en una sola hoja"
    text: "Junta todo lo de hoy en una sola hoja que le pueda dar a mi equipo: mi propósito, mi meta grande, mi visión en 5 puntos, mis 3 a 5 actividades diferenciadoras y las 3 tendencias a las que le apuesto. Escríbelo con mis palabras, sin palabras técnicas. Luego dime con honestidad qué partes se contradicen, cuál es un deseo que todavía no me he ganado y cuál haría más daño si me equivoco. Al final ordena mis aprendizajes por el impacto real si los ejecuto, y por cuál es el que mi equipo resistiría más en silencio."
  - title: "Haz que el cambio se quede"
    text: "Con todo lo de este chat, dame 10 tareas semanales, una por semana. Que cada una tome menos de una hora y cueste poco o nada, y que lleve mi estrategia del papel a algo que mi equipo sienta. Ordénalas para que los primeros logros generen confianza. Dime las 3 tareas que debo terminar antes de mi próxima reunión con mi grupo de seguimiento, y los 3 resultados que tendré amarrados en esta misma fecha del próximo trimestre. Luego crea las 10 tareas como archivo .ics, cada semana el [DÍA] a las [HORA], con por qué importa y cómo se ve terminada en la descripción. Si no puedes crear el archivo, dame una tabla que pueda pegar en mi calendario."
```

Cambios frente al original:
- «BHAG» pasa a «meta grande» (BHAG está prohibida en el archivo de esta hoja).
- «Core Purpose» pasa a «propósito»; «Vivid Vision» pasa a «visión».
- «accountability group» pasa a «grupo de seguimiento».
- «one page» pasa a «una sola hoja», porque la prueba prohíbe «pág».

**Nuevo — sin cambio al motor (respaldo)**

Se queda un solo prompt: «Haz que el cambio se quede», ya en versión 2026. Encaja con el paso
`compromiso` que ya existe. El prompt «Tu día en una sola hoja» se pierde hasta que exista la opción 2.

No recomiendo una hoja aparte «Haz que el cambio se quede»: repetiría el paso `compromiso`.

Pruebas que hay que cambiar en `tests/test_e87_tool_guides.py` (bloque de vision-summary):
- Hoy exige `set(ai_prompt) == {"text"}`. Con la lista, pasa a revisar cada elemento:
  claves dentro de `{"text", "title", "at"}`.
- Hoy busca «10 tareas». El texto nuevo dice «10 tareas semanales»: sigue pasando.
- Hoy prohíbe «pág» en el prompt. Por eso escribí «una sola hoja» y no «una página». Revisé: ninguno de los 2 textos trae «pág».
- Hoy prohíbe BHAG, Rocks y OPSP en todo el archivo. Ojo: el comentario YAML de la cita no puede
  nombrar el prompt como «BHAG». El comentario de arriba no lo hace.

---

## D. Mapa de cobertura 2026 (propuesto)

Hoy `tests/fixtures/e87-workbook-coverage.yaml` mapea el workbook 2025 (38 páginas). No hay mapa del 2026.

Propuesta: un archivo nuevo `tests/fixtures/workbook-2026-coverage.yaml`.

| Páginas 2026 | Hoja |
|---|---|
| p. 4 | swt (prompt de arranque) |
| p. 5–6 | swt |
| p. 7–8 | differentiating-activities |
| p. 17–18 | fanocracy (nueva) |
| p. 20 | vision-summary |
| resto (p. 9–16, mitad de p. 18, p. 19, p. 21–24) | pendiente. Por la agenda (p. 2) ahí van propósito, meta grande, visión y por qué personal. No las revisé página por página para este borrador |

ADVERTENCIA: la prueba contra copia compara con el texto 2025 (`metodologias_parsed/strategy_workbook.md`).
No existe el texto 2026 en el repo. Mientras no exista, nada revisa que las paráfrasis 2026 no copien
frases del original. Las paráfrasis de este borrador están en español, así que no comparten frases de 10 palabras con el inglés.
