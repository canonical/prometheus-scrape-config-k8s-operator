#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.
from __future__ import annotations

import logging
import pathlib

import jubilant
import pytest
import yaml
from helpers import get_config_values
from jubilant import Juju

# Cross-base upgrades (e.g. 24.04 -> 26.04) are not supported via juju refresh.
# The charmhub charm is built for 24.04 (Python 3.12), while the local charm
# targets 26.04 (Python 3.14). Juju refresh only replaces charm code, not the
# container image, so the old container's Python cannot load the new venv.
pytestmark = pytest.mark.skip(reason="Cross-base upgrade from 24.04 to 26.04 not supported")

logger = logging.getLogger(__name__)

METADATA = yaml.safe_load(pathlib.Path("./charmcraft.yaml").read_text())
app_name = METADATA["name"]


@pytest.mark.abort_on_fail
def test_config_values_are_retained_after_pod_upgraded(juju: Juju, charm: pathlib.Path):
    """Deploy from charmhub and then upgrade with the charm-under-test."""
    logger.info("deploy charm from charmhub")
    juju.deploy(app_name, channel="2/edge", base="ubuntu@24.04")

    # set some custom configs to later check they persisted across the test
    config = {"scrape_interval": "15s", "scrape_timeout": "10s"}
    juju.config(app_name, config)
    juju.wait(
        lambda status: (
            jubilant.all_blocked(status, app_name) and jubilant.all_agents_idle(status, app_name)
        ),
        timeout=1000,
    )

    logger.info("upgrade deployed charm with local charm %s", charm)
    juju.refresh(app_name, path=str(charm))
    juju.wait(
        lambda status: (
            jubilant.all_blocked(status, app_name) and jubilant.all_agents_idle(status, app_name)
        ),
        timeout=1000,
    )

    assert get_config_values(juju, app_name).items() >= config.items()
