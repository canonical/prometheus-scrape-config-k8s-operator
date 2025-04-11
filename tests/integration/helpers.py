#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

from typing import List, Literal, Optional

import aiohttp
from pytest_operator.plugin import OpsTest


class Prometheus:
    """A class that represents a running instance of Prometheus."""

    def __init__(self, host="localhost", port=9090):
        """Utility to manage a Prometheus application.

        Args:
            host: Optional; host address of Prometheus application.
            port: Optional; port on which Prometheus service is exposed.
        """
        self.base_url = f"http://{host}:{port}"

    async def is_ready(self) -> bool:
        """Send a GET request to check readiness.

        Returns:
          True if Prometheus is ready (returned 200 OK); False otherwise.
        """
        url = f"{self.base_url}/-/ready"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return response.status == 200

    async def config(self) -> str:
        """Send a GET request to get Prometheus configuration.

        Returns:
          YAML config in string format or empty string
        """
        url = f"{self.base_url}/api/v1/status/config"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                result = await response.json()
                return result["data"]["yaml"] if result["status"] == "success" else ""

    async def rules(self, rules_type: Optional[Literal["alert", "record"]] = None) -> list:
        """Send a GET request to get Prometheus rules.

        Args:
          rules_type: the type of rules to fetch, or all types if not provided.

        Returns:
          Rule Groups list or empty list
        """
        url = f"{self.base_url}/api/v1/rules{'?type=' + rules_type if rules_type else ''}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                result = await response.json()
                # response looks like this:
                # {"status":"success","data":{"groups":[]}
                return result["data"]["groups"] if result["status"] == "success" else []

    async def labels(self) -> List[str]:
        """Send a GET request to get labels.

        Returns:
          List of labels
        """
        url = f"{self.base_url}/api/v1/labels"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                result = await response.json()
                # response looks like this:
                # {
                #   "status": "success",
                #   "data": [
                #     "__name__",
                #     "alertname",
                #     "alertstate",
                #     ...
                #     "juju_application",
                #     "juju_charm",
                #     "juju_model",
                #     "juju_model_uuid",
                #     ...
                #     "version"
                #   ]
                # }
                return result["data"] if result["status"] == "success" else []

    async def alerts(self) -> List[dict]:
        """Send a GET request to get alerts.

        Returns:
          List of alerts
        """
        url = f"{self.base_url}/api/v1/alerts"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                result = await response.json()
                # response looks like this:
                #
                # {
                #   "status": "success",
                #   "data": {
                #     "alerts": [
                #       {
                #         "labels": {
                #           "alertname": "AlwaysFiring",
                #           "job": "non_existing_job",
                #           "juju_application": "avalanche-k8s",
                #           "juju_charm": "avalanche-k8s",
                #           "juju_model": "remotewrite",
                #           "juju_model_uuid": "5d2582f6-f8c9-4496-835b-675431d1fafe",
                #           "severity": "High"
                #         },
                #         "annotations": {
                #           "description": " of job non_existing_job is firing the dummy alarm.",
                #           "summary": "Instance  dummy alarm (always firing)"
                #         },
                #         "state": "firing",
                #         "activeAt": "2022-01-13T18:53:12.808550042Z",
                #         "value": "1e+00"
                #       }
                #     ]
                #   }
                # }
                return result["data"]["alerts"] if result["status"] == "success" else []


async def unit_address(ops_test: OpsTest, app_name: str, unit_num: int) -> str:
    """Find unit address for any application.

    Args:
        ops_test: pytest-operator plugin
        app_name: string name of application
        unit_num: integer number of a juju unit

    Returns:
        unit address as a string
    """
    assert ops_test.model
    status = await ops_test.model.get_status()
    return status["applications"][app_name]["units"][f"{app_name}/{unit_num}"]["address"]


async def get_prometheus_rules(ops_test: OpsTest, app_name: str, unit_num: int) -> list:
    """Fetch all Prometheus rules.

    Args:
        ops_test: pytest-operator plugin
        app_name: string name of Prometheus application
        unit_num: integer number of a Prometheus juju unit

    Returns:
        a list of rule groups.
    """
    host = await unit_address(ops_test, app_name, unit_num)
    prometheus = Prometheus(host=host)
    rules = await prometheus.rules()
    return rules


async def get_config_values(ops_test, app_name) -> dict:
    """Return the app's config, but filter out keys that do not have a value."""
    config = await ops_test.model.applications[app_name].get_config()
    return {key: config[key]["value"] for key in config if "value" in config[key]}
