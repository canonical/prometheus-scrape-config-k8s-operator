#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import asyncio
import logging

import pytest
from helpers import get_prometheus_rules

logger = logging.getLogger(__name__)

APP_NAME = "cos-config"
PROM_NAME = "prometheus"
SPRING_NAME = "spring-music"


@pytest.mark.abort_on_fail
async def test_build_and_deploy(ops_test, charm_under_test):
    await ops_test.model.deploy(charm_under_test, application_name=APP_NAME)
    # The charm should be in blocked state if not related to anything.
    await ops_test.model.wait_for_idle(status="blocked")


async def test_relate(ops_test):
    await asyncio.gather(
        ops_test.model.deploy("ch:prometheus-k8s", application_name=PROM_NAME, channel="beta"),
        ops_test.model.deploy("ch:spring-music", application_name=SPRING_NAME, channel="edge"),
    )
    await asyncio.gather(
        ops_test.model.add_relation(PROM_NAME, APP_NAME),
        ops_test.model.add_relation(APP_NAME, SPRING_NAME),
    )
    await ops_test.model.wait_for_idle(status="active")


async def test_alert_rules_exist(ops_test):
    rules = await get_prometheus_rules(ops_test=ops_test, app_name=PROM_NAME, unit_num=0)
    assert len(rules) > 0, "No alert rules are present even though spring music is related"


async def test_multiple_workloads_alert_rules(ops_test):
    old_rules = await get_prometheus_rules(ops_test=ops_test, app_name=PROM_NAME, unit_num=0)
    await ops_test.model.deploy(
        "ch:spring-music", application_name="spring-music2", channel="edge"
    )
    await ops_test.model.add_relation(APP_NAME, "spring-music2")
    await ops_test.model.wait_for_idle(status="active")
    new_rules = await get_prometheus_rules(ops_test=ops_test, app_name=PROM_NAME, unit_num=0)
    assert len(new_rules) > len(old_rules), "Additional workload instance did not add alert rules"
