# escala-health

## Propósito

Verificar que el Agente de Escalamiento está correctamente instalado y todos los componentes funcionan.

## Cuándo usarlo

- Después de instalar, para confirmar que todo quedó bien
- Si un skill no funciona, para diagnosticar el problema
- Periódicamente, para asegurar que el paquete Python está actualizado

## Pasos

### Paso 1: Verificar skills instalados

```bash
for dir in "$HOME/.claude/skills" "$HOME/.hermes/skills" "$HOME/.codex/skills"; do
    if [ -d "$dir" ]; then
        count=$(ls -d "$dir"/escala-* 2>/dev/null | wc -l | tr -d ' ')
        echo "  $dir: $count skills"
    fi
done
```

### Paso 2: Verificar paquete Python

```bash
if pip show escala-coaching &>/dev/null; then
    VERSION=$(pip show escala-coaching | grep Version | awk '{print $2}')
    LOCATION=$(pip show escala-coaching | grep Location | awk '{print $2}')
    echo "Paquete Python: escala-coaching v$VERSION en $LOCATION"
else
    echo "ERROR: Paquete Python escala-coaching NO instalado"
    echo "Solución: cd /ruta/al/repo && pip install -e ."
fi
```

### Paso 3: Probar imports

```bash
python3 -c "
try:
    from coaching.diagnose import run
    from coaching.level import run
    from coaching.progress import run
    from coaching.welcome import run
    from coaching.worksheet import run
    from validators.tasks import find_overdue
    from validators.session import validate_session_log
    print('✓ Todos los módulos importan correctamente')
except ImportError as e:
    print(f'ERROR: {e}')
"
```

### Paso 4: Versión del repo

```bash
REPO_PATH=$(cat "$HOME/.config/agente-de-escalamiento/repo-path" 2>/dev/null || echo "")
if [ -n "$REPO_PATH" ] && [ -d "$REPO_PATH/.git" ]; then
    cd "$REPO_PATH"
    echo "Versión: $(git rev-parse --short HEAD)"
    echo "Última actualización: $(cat $HOME/.config/agente-de-escalamiento/last-update 2>/dev/null || echo 'desconocido')"
fi
```

## Output

Resumen con ✅/❌ para skills, paquete Python, imports, y versión del repo.
