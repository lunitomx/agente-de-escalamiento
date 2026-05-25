#!/usr/bin/env python3
"""
Script de migración y anonimización de skills scaleup-* → escala-*
para el repositorio público Agente de Escalamiento.

Uso: python3 migrar-skills.py
"""

import os
import re
import shutil
import sys

# === CONFIGURACIÓN ===
REPO_ORIGEN = "/Users/soyahuehuetedigital/Documents/GitHub/ScaliingUPAI desarrollo/.claude/skills"
REPO_DESTINO = "/tmp/agente-de-escalamiento/escala-skills"

# Mapeo scaleup-* → escala-*
MAPEO_SKILLS = {
    "scaleup-cash": "escala-cash",
    "scaleup-cash-acceleration": "escala-cash-acceleration",
    "scaleup-cash-ccc": "escala-cash-ccc",
    "scaleup-cash-power1": "escala-cash-power1",
    "scaleup-close": "escala-close",
    "scaleup-close-capture": "escala-close-capture",
    "scaleup-close-log": "escala-close-log",
    "scaleup-close-sync": "escala-close-sync",
    "scaleup-context-add": "escala-context-add",
    "scaleup-context-query": "escala-context-query",
    "scaleup-dashboard": "escala-dashboard",
    "scaleup-diagnose": "escala-diagnose",
    "scaleup-execution": "escala-execution",
    "scaleup-execution-priorities": "escala-execution-priorities",
    "scaleup-execution-rhythms": "escala-execution-rhythms",
    "scaleup-execution-rockefeller": "escala-execution-habits",
    "scaleup-export": "escala-export",
    "scaleup-goal": "escala-goal",
    "scaleup-level": "escala-level",
    "scaleup-people": "escala-people",
    "scaleup-people-fac": "escala-people-fac",
    "scaleup-people-topgrading": "escala-people-topgrading",
    "scaleup-people-values": "escala-people-values",
    "scaleup-progress": "escala-progress",
    "scaleup-pulse": "escala-pulse",
    "scaleup-start": "escala-start",
    "scaleup-start-load-profile": "escala-start-load-profile",
    "scaleup-start-load-sessions": "escala-start-load-sessions",
    "scaleup-start-load-tasks": "escala-start-load-tasks",
    "scaleup-start-present": "escala-start-present",
    "scaleup-strategy": "escala-strategy",
    "scaleup-strategy-7strata": "escala-strategy-7strata",
    "scaleup-strategy-opsp": "escala-strategy-opsp",
    "scaleup-strategy-swot": "escala-strategy-swot",
    "scaleup-task-add": "escala-task-add",
    "scaleup-task-list": "escala-task-list",
    "scaleup-task-update": "escala-task-update",
    "scaleup-welcome": "escala-welcome",
    "scaleup-worksheet": "escala-worksheet",
}

# Diccionario inverso: escala-* → scaleup-*
MAPEO_INVERSO = {v: k for k, v in MAPEO_SKILLS.items()}

# Lista de nombres viejos ordenados por longitud descendente
# para evitar reemplazos parciales (scaleup-start antes que scaleup-start-load-profile)
NOMBRES_VIEJOS = sorted(MAPEO_SKILLS.keys(), key=len, reverse=True)
NOMBRES_NUEVOS = [MAPEO_SKILLS[n] for n in NOMBRES_VIEJOS]

# Tabla de reemplazos (en orden de aplicación)
REEMPLAZOS = [
    # 1. Referencias a otros skills (scaleup-foo → escala-foo)
    # Se maneja aparte con el mapeo de skills

    # 2. Nombres de proyectos y metodologías
    (r'\bScaleUp\b(?![\s-]*(?:Agent|AI|coaching|skills?))', 'Agente de Escalamiento'),
    (r'\bScaling Up\b', 'Escalamiento de Negocios'),
    (r'\bscaling up\b', 'escalamiento de negocios'),
    (r'\bscaling-up\b', 'escalamiento-de-negocios'),

    # 3. Conceptos específicos
    (r'\bRockefeller Habits\b', 'Hábitos de Ejecución'),
    (r'\bRockefeller habits\b', 'hábitos de Ejecución'),
    (r'\b10 Rockefeller Habits\b', '10 Hábitos de Ejecución'),
    (r'\bRockefeller Habits Checklist\b', 'Lista de Hábitos de Ejecución'),
    (r'\b7 Strata of Strategy\b', '7 Estratos de Estrategia'),

    # 4. Referencias a personas (atribución, no mención directa)
    (r'\bVerne Harnish\b', 'Verne Harnish (metodología original)'),

    # 5. Nombres de herramientas/metodologías
    (r'\bOne-Page Strategic Plan\b', 'Plan Estratégico de Una Página (OPSP)'),
    (r'\bOne-Page Strategic Plan \(OPSP\)\b', 'Plan Estratégico de Una Página (OPSP)'),
    (r'\bOPSP\b', 'Plan Estratégico de Una Página (OPSP)'),
    (r'\bFunction Accountability Chart\b', 'Mapa de Funciones y Responsabilidades'),
    (r'\bFunction Accountability Chart \(FAC\)\b', 'Mapa de Funciones y Responsabilidades (FACChart)'),
    (r'\bPower of One\b', 'Análisis Power of One'),
    (r'\bCash Conversion Cycle\b', 'Ciclo de Conversión de Efectivo (CCC)'),
    (r'\bSMART annual goal\b', 'Meta SMART anual'),
    (r'\bSMART goal\b', 'Meta SMART'),

    # 6. Paths absolutos
    (r'/Users/[^\s]+', '.'),
    (r'/home/[^\s]+', '.'),

    # 7. Nombres de proyecto interno
    (r'\bScaliingUPAI\b', 'Agente de Escalamiento'),

    # 8. Descripciones en frontmatter (name: scaleup-*)
    # Se maneja aparte
]

# Skills que usan el patrón `/scaleup-*` para invocar otros skills
def reemplazar_referencias_cruzadas(contenido, old_name, new_name):
    """Reemplaza referencias a scaleup-* dentro del contenido"""
    for v, n in zip(NOMBRES_VIEJOS, NOMBRES_NUEVOS):
        # Patrones de referencia: /scaleup-foo, scaleup-foo (al inicio de línea), `scaleup-foo`
        contenido = contenido.replace(f'/{v}', f'/{n}')
        contenido = contenido.replace(f'`{v}', f'`{n}')
        contenido = contenido.replace(f'name: {v}', f'name: {n}')
        contenido = contenido.replace(f'scaleup-{v.split("-", 1)[1] if "-" in v else v}', n)
    return contenido

def migrar_skill(old_name, new_name):
    """Migra un skill del nombre viejo al nuevo, anonimizando contenido."""
    src_dir = os.path.join(REPO_ORIGEN, old_name)
    dst_dir = os.path.join(REPO_DESTINO, new_name)

    if not os.path.isdir(src_dir):
        print(f"  ⚠ No existe: {src_dir}")
        return False

    # Crear directorio destino
    os.makedirs(dst_dir, exist_ok=True)

    # Leer SKILL.md original
    src_file = os.path.join(src_dir, "SKILL.md")
    if not os.path.isfile(src_file):
        print(f"  ⚠ No tiene SKILL.md: {src_file}")
        return False

    with open(src_file, "r", encoding="utf-8") as f:
        contenido = f.read()

    # ============================================
    # ANONIMIZACIÓN
    # ============================================

    # 1. Reemplazar nombre del skill en frontmatter
    contenido = contenido.replace(f'name: {old_name}', f'name: {new_name}')

    # 2. Reemplazar nombre en título (la primera línea #)
    contenido = re.sub(r'^# ScaleUp', '# Escalamiento', contenido, flags=re.MULTILINE)

    # 3. Reemplazar referencias a otros skills
    contenido = reemplazar_referencias_cruzadas(contenido, old_name, new_name)

    # 4. Aplicar tabla de reemplazos
    for patron, reemplazo in REEMPLAZOS:
        contenido = re.sub(patron, reemplazo, contenido)

    # 5. Reemplazar /scaleup-* en comandos e invocaciones
    for v, n in zip(NOMBRES_VIEJOS, NOMBRES_NUEVOS):
        contenido = contenido.replace(f'/{v}', f'/{n}')

    # 6. Reemplazar descripciones que contengan "ScaleUp"
    contenido = contenido.replace('ScaleUp ', 'Escalamiento ')
    contenido = contenido.replace('ScaleUp\n', 'Escalamiento\n')
    contenido = contenido.replace('ScaleUp\'s', 'del Agente de Escalamiento')

    # 7. Reemplazar paths .scaleup/ en referencias de comandos
    contenido = contenido.replace('.scaleup/', '.escala/')

    # 8. Reemplazar referencia a la identidad del agente
    contenido = contenido.replace('Eres ScaleUp', 'Eres el Agente de Escalamiento')
    contenido = contenido.replace('Eres un agente ScaleUp', 'Eres un Agente de Escalamiento')
    contenido = contenido.replace('ScaleUp agent', 'Agente de Escalamiento')

    # Escribir SKILL.md anonimizado
    dst_file = os.path.join(dst_dir, "SKILL.md")
    with open(dst_file, "w", encoding="utf-8") as f:
        f.write(contenido)

    return True


def main():
    total = len(MAPEO_SKILLS)
    ok = 0
    errors = []

    print(f"Migrando {total} skills de {REPO_ORIGEN} → {REPO_DESTINO}")
    print("=" * 70)

    for old_name, new_name in MAPEO_SKILLS.items():
        print(f"  {old_name:45s} → {new_name}")
        if migrar_skill(old_name, new_name):
            ok += 1
        else:
            errors.append(old_name)

    print("=" * 70)
    print(f"\nResultado: {ok}/{total} skills migrados exitosamente")

    if errors:
        print(f"Errores en: {', '.join(errors)}")

    # Verificar que no quedaron referencias no reemplazadas
    print("\n--- Verificación de anonimización ---")
    sospechosos = ["scaleup-", "Scaling Up", "rockefeller", "Verne Harnish",
                   "ScaliingUPAI", "/Users/", "Rockefeller Habits"]
    encontrados = 0
    for new_name in MAPEO_SKILLS.values():
        dst_file = os.path.join(REPO_DESTINO, new_name, "SKILL.md")
        if not os.path.isfile(dst_file):
            continue
        with open(dst_file, "r", encoding="utf-8") as f:
            contenido = f.read().lower()
        for s in sospechosos:
            if s.lower() in contenido:
                print(f"  ⚠ {new_name}: todavía contiene '{s}'")
                encontrados += 1

    if encontrados == 0:
        print("  ✅ Ninguna referencia sospechosa encontrada")
    else:
        print(f"\n  {encontrados} referencias sospechosas — revisar manualmente")

    return 0 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
