"""The manifest is what Home Assistant actually installs.

`requirements.txt` governs the development and CI environment only. When a dependency floor is
raised in one and not the other, CI happily proves the new version works while every real
instance keeps running the old one — which is how a raised `lxml` floor sat in
`requirements.txt` for two releases without reaching anybody.
"""

import json
from pathlib import Path

COMPONENT = Path(__file__).resolve().parent.parent
REPO_ROOT = COMPONENT.parent.parent


def _manifest_requirements() -> list[str]:
    manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))
    return sorted(manifest["requirements"])


def _txt_requirements() -> list[str]:
    lines = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    return sorted(line.strip() for line in lines if line.strip() and not line.startswith("#"))


def test_the_manifest_pins_what_requirements_txt_pins():
    """Both lists must agree, exactly — same packages, same floors."""
    assert _manifest_requirements() == _txt_requirements(), (
        "manifest.json and requirements.txt disagree. Home Assistant installs from the "
        "manifest, so a floor raised only in requirements.txt never ships."
    )
