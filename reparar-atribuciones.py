#!/usr/bin/env python3
"""Re-aplica atribuciones inline a skills usando open() directo (sin hermes_tools)."""
import os

BASE = "/tmp/agente-de-escalamiento/escala-skills"

ATRIBUCIONES = {
    "escala-cash": "el análisis Power of One, desarrollado por Verne Harnish",
    "escala-cash-acceleration": "el análisis Power of One, desarrollado por Verne Harnish",
    "escala-cash-power1": "el análisis Power of One, desarrollado por Verne Harnish",
    "escala-cash-ccc": "el Ciclo de Conversión de Efectivo, un principio de finanzas corporativas",
    "escala-close-capture": "los Hábitos de Ejecución, desarrollados por Verne Harnish como parte de su metodología de escalamiento de negocios",
    "escala-execution": "los Hábitos de Ejecución, desarrollados por Verne Harnish como parte de su metodología de escalamiento de negocios",
    "escala-execution-habits": "los Hábitos de Ejecución, desarrollados por Verne Harnish como parte de su metodología de escalamiento de negocios",
    "escala-goal": "el marco de metas SMART, desarrollado por George T. Doran",
    "escala-people": "el Mapa de Funciones y Responsabilidades, desarrollado por Verne Harnish",
    "escala-people-fac": "el Mapa de Funciones y Responsabilidades, desarrollado por Verne Harnish",
    "escala-people-topgrading": "la metodología Topgrading, desarrollada por Brad Smart",
    "escala-people-values": "el Plan Estratégico de Una Página (OPSP), desarrollado por Verne Harnish",
    "escala-pulse": "los Hábitos de Ejecución, desarrollados por Verne Harnish como parte de su metodología de escalamiento de negocios",
    "escala-strategy": "los 7 Estratos de Estrategia, desarrollados por Verne Harnish",
    "escala-strategy-7strata": "los 7 Estratos de Estrategia, desarrollados por Verne Harnish",
    "escala-strategy-opsp": "el Plan Estratégico de Una Página (OPSP), desarrollado por Verne Harnish",
    "escala-strategy-swot": "el Plan Estratégico de Una Página (OPSP), desarrollado por Verne Harnish",
}

count = 0
for skill_name, atribucion in ATRIBUCIONES.items():
    path = os.path.join(BASE, skill_name, "SKILL.md")
    if not os.path.isfile(path):
        print(f"  ⚠ No encontrado: {skill_name}")
        continue

    with open(path, "r", encoding="utf-8") as f:
        contenido = f.read()

    # Si ya tiene atribución, saltar
    if "ATTRIBUTIONS.md" in contenido:
        # Verificar que no tenga números de línea corruptos
        if "|---" in contenido and "|name:" not in contenido:
            pass  # clean, skip
        else:
            print(f"  ~ {skill_name}: ya tiene atribución (limpio)")
        continue

    footer = f"\n\n---\n*Esta herramienta está inspirada en {atribucion}. Ver [ATTRIBUTIONS.md](../ATTRIBUTIONS.md) para la referencia completa.*\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(contenido.rstrip() + footer)
    count += 1
    print(f"  + {skill_name}")

print(f"\n{count} skills con atribución agregada (vía open() directo)")

# Verificación de limpieza
print("\n--- Verificación de integridad ---")
for skill_name in ATRIBUCIONES:
    path = os.path.join(BASE, skill_name, "SKILL.md")
    with open(path, "r", encoding="utf-8") as f:
        first = f.readline()
    if first.startswith("    ") and "|---" in first:
        print(f"  ⚠ CORRUPTO: {skill_name}")
    else:
        pass  # clean

print("  (solo muestra corruptos - si no hay output, todos OK)")
