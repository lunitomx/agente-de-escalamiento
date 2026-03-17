# Epic Brief: E3 — Agent Framework

## Hypothesis

Si creamos un CLAUDE.md del producto con identidad ScaleUp, conectamos los 19 skills via slash commands, y limpiamos el repo para distribución, entonces cualquier empresario podrá clonar el repo, abrir Claude Code, y tener un agente ScaleUp experto funcionando sin configuración adicional.

## Success Metrics

| Metric | Target |
|--------|--------|
| Tiempo de setup | < 5 minutos (clone + abrir Claude Code) |
| Skills accesibles | 19/19 skills invocables via slash commands |
| Flujo completo | welcome → diagnose → sub-agent funciona sin errores |
| Zero config | No requiere API keys, instalaciones, ni dependencias externas |

## Appetite

5 stories, tamaño total M. Sin código — todo es configuración de Claude Code (markdown, yaml, gitignore).

## Rabbit Holes

- No construir CLI installer (pip/npm) — el repo ES el producto, se clona y funciona
- No agregar tests automatizados de skills — la validación es manual (E4)
- No crear documentación extensa — README conciso con quick start
