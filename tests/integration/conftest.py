# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import logging

import pytest
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
async def charm_under_test(ops_test: OpsTest):
    """Charm used for integration testing."""
    count = 0
    # Intermittent issue where charmcraft fails to build the charm for an unknown reason.
    # Retry building the charm
    while True:
        try:
            charm = await ops_test.build_charm(".")
            return charm
        except RuntimeError:
            logger.warning("Failed to build charm. Trying again!")
            count += 1
            if count == 3:
                raise
