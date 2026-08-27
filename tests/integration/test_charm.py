#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

from __future__ import annotations

import logging
import pathlib

import jubilant
import pytest
from helpers import get_prometheus_rules
from jubilant import Juju

logger = logging.getLogger(__name__)

APP_NAME = "prometheus-scrape-config"
PROM_NAME = "prometheus"
ZINC_NAME = "zinc"


@pytest.mark.abort_on_fail
def test_dependencies(juju: Juju):
    juju.deploy("prometheus-k8s", app=PROM_NAME, channel="dev/edge", trust=True)
    juju.deploy("zinc-k8s", app=ZINC_NAME, channel="edge")
    juju.deploy("zinc-k8s", app="zinc2", channel="edge")
    juju.wait(jubilant.all_active, timeout=1000)


def test_build_and_deploy(juju: Juju, charm: pathlib.Path):
    juju.deploy(charm, app=APP_NAME)
    # The charm should be in blocked state if not related to anything.
    juju.wait(lambda status: jubilant.all_blocked(status, APP_NAME), timeout=1000)


def test_relate(juju: Juju):
    juju.integrate(f"{PROM_NAME}:metrics-endpoint", f"{APP_NAME}:metrics-endpoint")
    juju.integrate(f"{APP_NAME}:configurable-scrape-jobs", f"{ZINC_NAME}:metrics-endpoint")
    juju.wait(jubilant.all_active, timeout=1000)


def test_alert_rules_exist(juju: Juju):
    rules = get_prometheus_rules(juju=juju, app_name=PROM_NAME, unit_num=0)
    assert len(rules) > 0, "No alert rules are present even though zinc is related"


def test_multiple_workloads_alert_rules(juju: Juju):
    old_rules = get_prometheus_rules(juju=juju, app_name=PROM_NAME, unit_num=0)
    juju.integrate(APP_NAME, "zinc2")
    juju.wait(jubilant.all_active, timeout=1000)
    new_rules = get_prometheus_rules(juju=juju, app_name=PROM_NAME, unit_num=0)
    assert len(new_rules) > len(old_rules), "Additional workload instance did not add alert rules"


def test_non_leader_units_set_waiting_status(juju: Juju):
    juju.cli("scale-application", APP_NAME, "2")
    juju.wait(lambda status: len(status.apps[APP_NAME].units) == 2, timeout=1000)
    juju.wait(jubilant.all_agents_idle, timeout=1000)
    statuses = [
        unit.workload_status.current for unit in juju.status().apps[APP_NAME].units.values()
    ]
    assert len(statuses) == 2
    assert "active" in statuses
    assert "waiting" in statuses
