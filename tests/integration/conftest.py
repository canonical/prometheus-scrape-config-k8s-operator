# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
import os
from pathlib import Path

import pytest
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
async def charm_under_test(ops_test: OpsTest):
    """Charm used for the pytest-operator (OpsTest) integration tests."""
    if charm_file := os.environ.get("CHARM_PATH"):
        return Path(charm_file)

    charm = await ops_test.build_charm(".")
    return charm


@pytest.fixture(scope="session")
def charm() -> Path:
    """Packed charm for the jubilant tests: ``CHARM_PATH``, else a local ``*.charm``."""
    if charm_file := os.environ.get("CHARM_PATH"):
        return Path(charm_file).resolve()

    charms = list(Path(".").glob("*.charm"))
    assert charms, "No *.charm found; run `charmcraft pack` or set CHARM_PATH"
    assert len(charms) == 1, f"Found more than one charm, cannot pick: {charms}"
    return charms[0].resolve()
