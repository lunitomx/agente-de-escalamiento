---
description: 'Onboarding para ScaleUp Agent AI. Recoge perfil de empresa y prepara contexto para diagnóstico.'
name: scaleup-welcome
---

# ScaleUp Welcome

## Purpose

Dar la bienvenida, recoger info de la empresa y guardar el perfil usando el core Python cross-platform.

## Architecture

Este skill es un **adapter delgado** que invoca el core module en `.scaleup/coaching/welcome/`.
La lógica de negocio (validación, stage detection, persistencia) vive en Python, no en SKILL.md.

## Steps

### Step 1: Check Existing Profile

```bash
test -f .scaleup/agent/memory/company-profile.yaml && echo "EXISTS" || echo "NEW"
```

| Result | Action |
|--------|--------|
| EXISTS | Show existing profile, offer `/scaleup-diagnose` |
| NEW | Continue to Step 2 |

### Step 2: Company Intake

Preguntar de forma conversacional:
1. **Nombre de la empresa**
2. **Industria / sector**
3. **Número de empleados** (aproximado)
4. **Etapa:** startup / growth / scaling / expansion
5. **Metodología de entrada:** lean-canvas (startup/reinventando) o bmc (crecimiento)

### Step 3: Invoke Core Module

```bash
echo '{"company_name": "Nombre", "industry": "Sector", "employees": 15, "entry_methodology": "lean-canvas", "base_path": ".scaleup"}' | python3 -c "
import sys, json
sys.path.insert(0, '.')
from scaleup.coaching.welcome import run
ctx = json.loads(sys.stdin.read())
result = run(ctx)
print(json.dumps(result, indent=2, ensure_ascii=False))
"
```

### Step 4: Quality Gate

```bash
python3 .scaleup/agent/validators/welcome.py .scaleup/agent/memory/company-profile.yaml
```

| Result | Action |
|--------|--------|
| VALIDATION PASSED | Present welcome message |
| VALIDATION FAILED | Show errors, ask user to correct |

### Step 5: Present Result

Mostrar el `output` del core module al usuario.

## Output

| Item | Destination |
|------|-------------|
| Company profile | `.scaleup/agent/memory/company-profile.yaml` |
| Next | `/scaleup-diagnose` |
