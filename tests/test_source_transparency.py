from __future__ import annotations

from pathlib import Path

from validators.public_boundary import load_public_boundary_policy, scan_public_content


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
POLICY = ROOT / "governance/public-boundary.yaml"


def test_public_readme_declares_independence_without_prohibited_identity() -> None:
    text = README.read_text(encoding="utf-8")
    policy = load_public_boundary_policy(POLICY)

    assert "ESCALA es un producto independiente." in text
    assert "No es un producto oficial" in text
    assert "oficial ni está\nafiliado, patrocinado, aprobado o respaldado" in text
    assert scan_public_content("README.md", text.encode("utf-8"), policy) == []


def test_independence_notice_does_not_claim_distribution_authority() -> None:
    text = README.read_text(encoding="utf-8")

    assert "aportar no crean\nuna relación oficial ni autorizan su distribución" in text
