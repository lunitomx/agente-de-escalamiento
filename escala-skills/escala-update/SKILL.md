# escala-update

## Propósito

Actualizar los skills del Agente de Escalamiento desde GitHub. Lee la ruta del repo guardada por `install.sh`, hace `git pull` y reinstala.

## Cuándo usarlo

- El usuario quiere la versión más reciente de los skills
- Aparecen nuevos skills o fixes en el repo
- El usuario ejecuta `/escala-update`

## Pasos

### Paso 1: Leer ruta del repo

```bash
REPO_PATH=$(cat "$HOME/.config/agente-de-escalamiento/repo-path" 2>/dev/null || echo "")
if [ -z "$REPO_PATH" ]; then
    echo "ERROR: No se encontró ruta del repo."
    echo "Ejecuta install.sh primero desde el repositorio clonado."
    echo "  git clone https://github.com/lunitomx/agente-de-escalamiento.git"
    echo "  cd agente-de-escalamiento && ./install.sh"
    exit 1
fi
```

### Paso 2: Git pull

```bash
cd "$REPO_PATH"
echo "→ Repositorio: $REPO_PATH"

# Guardar hash actual para mostrar cambios
BEFORE=$(git rev-parse HEAD)

# Traer cambios
git pull origin main 2>&1 || git pull origin master 2>&1 || {
    echo "ERROR: No se pudo actualizar. Revisa tu conexión o si tienes permisos."
    exit 1
}

AFTER=$(git rev-parse HEAD)
```

### Paso 3: Mostrar qué cambió

```bash
if [ "$BEFORE" = "$AFTER" ]; then
    echo "✓ Ya tienes la versión más reciente."
else
    echo "→ Cambios recibidos:"
    git log --oneline "$BEFORE..$AFTER" 2>/dev/null | head -20
    echo ""
fi
```

### Paso 4: Reinstalar skills

```bash
bash install.sh
```

### Paso 5: Guardar timestamp

```bash
date -u +%Y-%m-%dT%H:%M:%SZ > "$HOME/.config/agente-de-escalamiento/last-update"
echo "✓ Última actualización: $(cat $HOME/.config/agente-de-escalamiento/last-update)"
```

## Output

| Item | Descripción |
|------|-------------|
| Estado | Actualizado o ya en última versión |
| Cambios | Lista de commits nuevos (si los hay) |
| Skills reinstalados | Skills copiados a las plataformas |

## Notas

- Requiere haber ejecutado `install.sh` al menos una vez (guarda la ruta)
- Si moviste el repo de carpeta, ejecuta `install.sh` de nuevo para actualizar la ruta
- El repo debe estar clonado con HTTPS (git clone), no descargado como ZIP
