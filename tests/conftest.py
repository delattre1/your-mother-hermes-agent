import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parent.parent / "skills" / "mother-checkup" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from mother.store import MotherStore  # noqa: E402


@pytest.fixture()
def home(tmp_path):
    return str(tmp_path / "mother")


@pytest.fixture()
def store(home):
    return MotherStore(home)
