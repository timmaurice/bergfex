"""The scheduled scripts must run on a machine with no Home Assistant.

`live_check.yml` and `season_watch.yml` deliberately install only
`requirements.txt` - pulling the whole core in to check a page shape would be
absurd, and would drag the core-version resolution into two jobs that have no
opinion about it. So both scripts have to reach the integration's parser and
constants without the integration's runtime.

That is easy to break from a distance and impossible to notice: the jobs run on
a schedule, one of them at 02:00, and neither is attached to a pull request.
Adding `import homeassistant.helpers.config_validation as cv` and
`from .config_flow import entry_area_name` to the package `__init__` broke both,
and the suite stayed green because the suite runs with Home Assistant installed.

These tests are the missing check. They run in a subprocess, because the only
faithful way to test "Home Assistant is absent" is for it to actually be absent.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# voluptuous comes with Home Assistant and is imported by config_flow, which the
# package __init__ imports. A machine without the core has neither.
BLOCKED = ("homeassistant", "voluptuous")

PROGRAM = """
import sys

BLOCKED = {blocked!r}


class Blocker:
    \"\"\"Make the core genuinely unimportable, as it is on the runners.\"\"\"

    @staticmethod
    def find_spec(fullname, path=None, target=None):
        root = fullname.split(".")[0]
        if root in BLOCKED:
            raise ImportError(f"{{fullname}} is not installed")
        return None


sys.meta_path.insert(0, Blocker())
for name in list(sys.modules):
    if name.split(".")[0] in BLOCKED:
        del sys.modules[name]

import importlib.util

spec = importlib.util.spec_from_file_location("script_under_test", {script!r})
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Reached the real integration code, not a stand-in.
assert module.{symbol}, "{symbol} is missing"
for name in sys.modules:
    assert name.split(".")[0] not in BLOCKED, f"{{name}} was faked into sys.modules"

print("OK")
"""


@pytest.mark.parametrize(
    ("script", "symbol"),
    [
        ("scripts/check_season_start.py", "parse_resort_page"),
        ("scripts/check_live_site.py", "KEYWORDS"),
    ],
)
def test_the_script_runs_without_home_assistant(script, symbol):
    """Importing the script must not need the core, or fake it either.

    Faking it would be worse than failing: a stub answers every attribute, so the
    script would go on comparing live pages against mocks and reporting success.
    """
    program = PROGRAM.format(
        blocked=BLOCKED, script=str(REPO_ROOT / script), symbol=symbol
    )

    result = subprocess.run(
        [sys.executable, "-c", program],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        f"{script} cannot be imported without Home Assistant:\n"
        f"{result.stdout}\n{result.stderr}"
    )
    assert "OK" in result.stdout
