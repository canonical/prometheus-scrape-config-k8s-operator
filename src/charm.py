#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Prometheus Scrape Configuration charm.

The Prometheus Scrape Configuration charm
allows overriding configuration of scrape jobs
from any metrics provider that provides these metrics
through the 'metrics-endpoint' relation using the
`prometheus_scrape` interface.
"""

import json
import logging

import yaml
from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointConsumer
from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus

logger = logging.getLogger(__name__)


class PrometheusScrapeConfigCharm(CharmBase):
    """PrometheusScrapeConfigCharm is an adapter charm used to override configuration settings in a scrape job."""

    def __init__(self, *args):
        """Construct the charm."""
        super().__init__(*args)

        self._metrics_provider_relation_name = "configurable-scrape-jobs"
        self._metrics_consumer_relation_name = "metrics-endpoint"
        self._forward_alert_rules = self.config["forward_alert_rules"]

        # The metrics consumer object in this charm also acts as the metrics provider for other metrics
        # consumer charms related with this charm, hence we label the metrics consumer object in this charm
        # as the `_metrics_providers`.
        self._metrics_providers = MetricsEndpointConsumer(
            self, self._metrics_provider_relation_name
        )

        consumer_events = self.on[self._metrics_consumer_relation_name]
        provider_events = self.on[self._metrics_provider_relation_name]

        for e in [
            self.on.start,
            self.on.config_changed,
            self.on.upgrade_charm,
            self._metrics_providers.on.targets_changed,
            provider_events.relation_created,
            provider_events.relation_joined,
            provider_events.relation_broken,
            consumer_events.relation_created,
            consumer_events.relation_changed,
        ]:
            self.framework.observe(e, self._update_all_metrics_consumers)

        self.framework.observe(self.on.install, self._on_install)

    def _on_install(self, _) -> None:
        """Do any initial charm startup operations."""
        self.unit.set_workload_version("n/a")

    def _update_all_metrics_consumers(self, _):
        """Update all scrape configuration jobs for all metrics consumers."""
        logger.debug("Updating all metrics consumers")

        if not self.unit.is_leader():
            self.unit.status = WaitingStatus("inactive unit")
            return

        if not self._has_consumers():
            self.unit.status = BlockedStatus("missing metrics consumer (relate to prometheus?)")
            return

        if not self._has_providers():
            self.unit.status = BlockedStatus(
                "missing metrics provider (relate to upstream charm?)"
            )
            return

        self.unit.status = MaintenanceStatus(
            "Updating scrape jobs and alert rules for all metrics consumer"
        )

        for relation in self.model.relations[self._metrics_consumer_relation_name]:
            self._update_metrics_consumer_relation(relation)

        self.unit.status = ActiveStatus()

    def _update_metrics_consumer_relation(self, metrics_consumer_relation):
        """Ensure that a specific metrics consumer's job specifications are updated."""
        if not self.unit.is_leader():
            self.unit.status = WaitingStatus("inactive unit")
            return

        if not metrics_consumer_relation:
            logger.debug("no metrics consumer relation provided")
            return

        prometheus_configurations = self._prometheus_configurations

        scrape_jobs = json.dumps(prometheus_configurations["scrape_jobs"])
        alert_rules = json.dumps(prometheus_configurations["alert_rules"])

        metrics_consumer_relation.data[self.app]["scrape_jobs"] = scrape_jobs
        metrics_consumer_relation.data[self.app]["alert_rules"] = alert_rules
        logger.debug("Updated metrics consumer %s", metrics_consumer_relation.app)

    @property
    def _prometheus_configurations(self):
        """Fetch all scrape jobs with updated configuration.

        This method transforms all scrape jobs provided by related
        metrics consumers, using configuration items set in this
        charm. The scrape jobs (including associated alert rules)
        are returned.
        """
        yaml_keys = ["relabel_configs", "metric_relabel_configs"]
        config = {k: v for k, v in self.model.config.items() if k not in yaml_keys}
        for key in yaml_keys:
            if as_yaml := self.model.config.get(key):
                config[key] = yaml.safe_load(str(as_yaml))

        configured_jobs = []
        for job in self._metrics_providers.jobs():
            job.update(config)
            configured_jobs.append(job)

        alerts = list(self._metrics_providers.alerts.values())
        alert_groups = {"groups": []}  # type: ignore
        if self._forward_alert_rules:
            for entry in alerts:
                alert_groups["groups"] += entry["groups"]

        return {
            "scrape_jobs": configured_jobs,
            "alert_rules": alert_groups if alert_groups["groups"] else {},
        }

    def _has_providers(self):
        """Checks if there is at least one metrics provider related to the charm."""
        return (
            self._metrics_provider_relation_name in self.model.relations
            and self.model.relations[self._metrics_provider_relation_name]
        )

    def _has_consumers(self):
        """Checks if there is at least one metrics consumer related to the charm."""
        return (
            self._metrics_consumer_relation_name in self.model.relations
            and self.model.relations[self._metrics_consumer_relation_name]
        )


if __name__ == "__main__":
    main(PrometheusScrapeConfigCharm)
