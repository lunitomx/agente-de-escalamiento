"""S86.38 — el requisito de instalación dice cómo se instala ESCALA de verdad.

Desde S86.35 el dueño instala con la línea del README: `instalar.sh` clona el
repositorio público con git en ~/ESCALA y corre
`install.sh --platform claude --with-specialists`. Pegar la línea otra vez
actualiza con `git pull --ff-only`. En Windows no hay instalación nativa:
`instalar.sh` se detiene y pide WSL2.

Estas pruebas fallan si el texto del libro maestro vuelve a decir que la
instalación no es un clon del repositorio, o si deja de coincidir con el README
y con `instalar.sh`.
"""

from __future__ import annotations

from pathlib import Path
import re

from validators.master_acceptance import load_master_acceptance_ledger

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = (
    ROOT / "work/epics/e36-product-truth-ip-governance/master-acceptance-ledger.yaml"
)
README = ROOT / "README.md"
INSTALAR = ROOT / "instalar.sh"

# Frase del requisito → (archivo que la respalda, texto que debe estar ahí).
MACOS_PIECES: dict[str, tuple[Path, str]] = {
    "instalar.sh": (README, "/main/instalar.sh | sh"),
    "git clone": (INSTALAR, 'git clone --quiet "$REPO_URL" "$ESCALA_DIR"'),
    "~/ESCALA": (README, "deja ESCALA en `~/ESCALA`"),
    "install.sh --platform claude --with-specialists": (
        INSTALAR,
        "./install.sh --platform claude --with-specialists",
    ),
    "same line again updates": (
        README,
        "Para actualizar, pega otra vez la misma línea",
    ),
    "git pull --ff-only": (INSTALAR, "pull --ff-only"),
}
WINDOWS_PIECES: dict[str, tuple[Path, str]] = {
    "no native install": (INSTALAR, "ESCALA todavía no se instala directo en Windows."),
    "WSL2": (README, "(en Windows, WSL2)"),
    "same line": (INSTALAR, "pega ahí el mismo comando"),
}
# «no repository-development layout», «without a repository», «not a clone»…
_DENIES_CLONE = re.compile(
    r"\b(?:no|not|without)\b[^.;:]*\b(?:repositor\w*|clone|git)\b", re.IGNORECASE
)


def _acceptance(requirement_id: str) -> str:
    ledger = load_master_acceptance_ledger(LEDGER_PATH)
    return next(
        item.acceptance for item in ledger.requirements if item.id == requirement_id
    )


def test_patron_atrapa_el_texto_viejo_y_no_el_nuevo() -> None:
    viejo = (
        "A fresh supported macOS machine can install the qualified local package "
        "with one documented flow and no repository-development layout."
    )
    assert _DENIES_CLONE.search(viejo)
    assert _DENIES_CLONE.search("It installs without a git repository.")
    assert _DENIES_CLONE.search(_acceptance("REQ-E41-001")) is None


def test_macos_dice_que_la_linea_unica_clona_el_repositorio() -> None:
    texto = _acceptance("REQ-E41-001")
    faltan = [frase for frase in MACOS_PIECES if frase not in texto]
    assert faltan == []


def test_windows_dice_la_verdad_wsl2_sin_instalador_nativo() -> None:
    texto = _acceptance("REQ-E41-002")
    faltan = [frase for frase in WINDOWS_PIECES if frase not in texto]
    assert faltan == []


def test_cada_frase_del_requisito_sigue_en_readme_o_instalar() -> None:
    sin_respaldo = [
        f"{frase} → {archivo.name}: {aguja}"
        for frase, (archivo, aguja) in {**MACOS_PIECES, **WINDOWS_PIECES}.items()
        if aguja not in archivo.read_text(encoding="utf-8")
    ]
    assert sin_respaldo == []
