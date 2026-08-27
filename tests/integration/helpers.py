#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

from typing import List, Literal, Optional

import requests
from jubilant import Juju


class Prometheus:
    """A class that represents a running instance of Prometheus."""

    def __init__(self, host="localhost", port=9090):
        """Utility to manage a Prometheus application.

        Args:
            host: Optional; host address of Prometheus application.
            port: Optional; port on which Prometheus service is exposed.
        """
        self.base_url = f"http://{host}:{port}"

    def is_ready(self) -> bool:
        """Send a GET request to check readiness.

        Returns:
          True if Prometheus is ready (returned 200 OK); False otherwise.
        """
        url = f"{self.base_url}/-/ready"
        response = requests.get(url, timeout=10)
        return response.status_code == 200

    def config(self) -> str:
        """Send a GET request to get Prometheus configuration.

        Returns:
          YAML config in string format or empty string
        """
        url = f"{self.base_url}/api/v1/status/config"
        result = requests.get(url, timeout=10).json()
        return result["data"]["yaml"] if result["status"] == "success" else ""

    def rules(self, rules_type: Optional[Literal["alert", "record"]] = None) -> list:
        """Send a GET request to get Prometheus rules.

        Args:
          rules_type: the type of rules to fetch, or all types if not provided.

        Returns:
          Rule Groups list or empty list
        """
        url = f"{self.base_url}/api/v1/rules{'?type=' + rules_type if rules_type else ''}"
        result = requests.get(url, timeout=10).json()
        # response looks like this:
        # {"status":"success","data":{"groups":[]}
        return result["data"]["groups"] if result["status"] == "success" else []

    def labels(self) -> List[str]:
        """Send a GET request to get labels.

        Returns:
          List of labels
        """
        url = f"{self.base_url}/api/v1/labels"
        result = requests.get(url, timeout=10).json()
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

    def alerts(self) -> List[dict]:
        """Send a GET request to get alerts.

        Returns:
          List of alerts
        """
        url = f"{self.base_url}/api/v1/alerts"
        result = requests.get(url, timeout=10).json()
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


def unit_address(juju: Juju, app_name: str, unit_num: int) -> str:
    """Find unit address for any application.

    Args:
        juju: jubilant Juju instance
        app_name: string name of application
        unit_num: integer number of a juju unit

    Returns:
        unit address as a string
    """
    status = juju.status()
    return status.apps[app_name].units[f"{app_name}/{unit_num}"].address


def get_prometheus_rules(juju: Juju, app_name: str, unit_num: int) -> list:
    """Fetch all Prometheus rules.

    Args:
        juju: jubilant Juju instance
        app_name: string name of Prometheus application
        unit_num: integer number of a Prometheus juju unit

    Returns:
        a list of rule groups.
    """
    host = unit_address(juju, app_name, unit_num)
    prometheus = Prometheus(host=host)
    return prometheus.rules()


def get_config_values(juju: Juju, app_name: str) -> dict:
    """Return the app's config, but filter out keys that do not have a value."""
    return dict(juju.config(app_name) or {})
