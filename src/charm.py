#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Prometheus Scrape Configuration
"""

import json
import logging

from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointConsumer
from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus

logger = logging.getLogger(__name__)


class PrometheusScrapeConfigCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)

        self._target_relation = "configurable-scrape-jobs"
        self._prometheus_relation = "metrics-endpoint"

        # manages relation with scrape targets
        self._metrics_consumer = MetricsEndpointConsumer(self, self._target_relation)
        self.framework.observe(
            self._metrics_consumer.on.targets_changed, self._update_prometheus_jobs
        )

        # manages relation with Prometheus charm
        self.framework.observe(
            self.on[self._prometheus_relation].relation_joined, self._set_prometheus_jobs
        )
        self.framework.observe(
            self.on[self._prometheus_relation].relation_changed, self._update_prometheus_jobs
        )

        # manages configuration changes for this charm
        self.framework.observe(self.on.config_changed, self._update_prometheus_jobs)
        self.framework.observe(self.on.show_config_action, self._on_show_config_action)

    def _set_prometheus_jobs(self, event):
        """Set Prometheus scrape configuration for all targets.
        """
        self.unit.status = ActiveStatus()
        if not self.unit.is_leader():
            return

        jobs = self._metrics_consumer.jobs()
        for job in jobs:
            job.update(self._config)
        event.relation.data[self.app]["scrape_jobs"] = json.dumps(jobs)

        groups = list(self._metrics_consumer.alerts().values())
        event.relation.data[self.app]["alert_rules"] = json.dumps({"groups": groups})

    def _update_prometheus_jobs(self, _):
        """Update all scrape configuration jobs.
        """
        self.unit.status = ActiveStatus()
        if not self.unit.is_leader():
            return

        for relation in self.model.relations[self._prometheus_relation]:
            jobs = self._metrics_consumer.jobs()
            for job in jobs:
                job.update(self._config)
            relation.data[self.app]["scrape_jobs"] = json.dumps(jobs)

            groups = list(self._metrics_consumer.alerts().values())
            relation.data[self.app]["alert_rules"] = json.dumps({"groups": groups})

    def _on_show_config_action(self, event):
        """Show current set of configured options.
        """
        event.set_results(self._config)

    @property
    def _config(self):
        return {key.replace('-', '_'): value for key, value in self.model.config.items()}


if __name__ == "__main__":
    main(PrometheusScrapeConfigCharm)
