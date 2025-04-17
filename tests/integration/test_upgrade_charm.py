#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.


import logging
from pathlib import Path

import pytest
import yaml
from helpers import get_config_values
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)

METADATA = yaml.safe_load(Path("./charmcraft.yaml").read_text())
app_name = METADATA["name"]


@pytest.mark.abort_on_fail
async def test_config_values_are_retained_after_pod_upgraded(ops_test: OpsTest, charm_under_test):
    """Deploy from charmhub and then upgrade with the charm-under-test."""
    assert ops_test.model
    logger.info("deploy charm from charmhub")
    await ops_test.model.deploy(
        f"ch:{app_name}",
        application_name=app_name,
        channel="edge",
        base="ubuntu@20.04",
    )

    # set some custom configs to later check they persisted across the test
    config = {"scrape_interval": "15s", "scrape_timeout": "10s"}
    await ops_test.model.applications[app_name].set_config(config)
    await ops_test.model.wait_for_idle(apps=[app_name], status="blocked", timeout=1000)

    logger.info("upgrade deployed charm with local charm %s", charm_under_test)
    await ops_test.model.applications[app_name].refresh(path=charm_under_test)
    await ops_test.model.wait_for_idle(apps=[app_name], status="blocked", timeout=1000)

    assert (await get_config_values(ops_test, app_name)).items() >= config.items()
