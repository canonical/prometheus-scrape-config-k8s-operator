#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Prometheus Scrape Configuration charm.

The Prometheus Scrape Configuration charm
allows overriding configuration of scrape jobs
from any metrics provider the provides these metrics
through the 'metrics-endpoint' relation using the
`prometheus_scrape` interface.
"""

import json
import logging

from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointConsumer
from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus

logger = logging.getLogger(__name__)


class PrometheusScrapeConfigCharm(CharmBase):
    """PrometheusScrapeConfigCharm is a adapter charm.

    PrometheusScrapeConfigCharm has no real workload. It
    transforms incoming scrape jobs from metrics providers i.e scrape
    targets (e.g., charms that expose a metrics endpoint) and pushes them
    to metrics consumer charms (e.g., a Prometheus charm)
    that will execute the metrics scraping.
    """

    def __init__(self, *args):
        """Construct the charm."""
        super().__init__(*args)

        self._metrics_provider_relation_name = "configurable-scrape-jobs"
        self._metrics_consumer_relation_name = "metrics-endpoint"

        # Use a metrics consumer object to manage relations with all metrics provider charms
        # related to this charm. Note the metrics consumer object in this charm also acts
        # as the metrics provider for other metrics consumer charms related with this charm,
        # hence we label the metrics consumer object in this charm as the `_metrics_providers`.
        self._metrics_providers = MetricsEndpointConsumer(self, self._metrics_provider_relation_name)

        # when list of metrics providers change notify all metrics consumers
        self.framework.observe(
            self._metrics_providers.on.targets_changed,
            self._update_all_metrics_consumers,
        )

        # when a metrics provider goes away updated all metrics consumers
        self.framework.observe(
            self.on[self._metrics_provider_relation_name].relation_broken,
            self._on_metrics_provider_relation_broken,
        )

        # When a new consumer of the metrics-endpoint relation is related,
        # pass it all the current scrape jobs. We register to both the relation
        # being created and joined, because relation_created is not reliably sent
        # over unit recreation.
        self.framework.observe(
            self.on[self._metrics_consumer_relation_name].relation_created,
            self._update_new_metrics_consumer,
        )
        self.framework.observe(
            self.on[self._prometheus_relation_name].relation_joined,
            self._set_jobs_to_new_downstream,
        )

        # manages configuration changes for this charm
        self.framework.observe(self.on.config_changed, self._update_all_metrics_consumers)
        # Ensure we refresh scrape jobs on charm upgrade
        self.framework.observe(self.on.upgrade_charm, self._update_all_metrics_consumers)

    def _has_metrics_providers(self):
        return (
            self._metrics_provider_relation_name in self.model.relations
            and self.model.relations[self._metrics_provider_relation_name]
        )

    def _has_metrics_consumers(self):
        return (
            self._metrics_consumer_relation_name in self.model.relations
            and self.model.relations[self._metrics_consumer_relation_name]
        )

    def _on_metrics_provider_relation_broken(self, _):
        """Block the charm when no charms contribute scrape jobs."""
        if not self.unit.is_leader():
            return

        if not self._has_metrics_providers():
            self.unit.status = BlockedStatus("missing metrics provider")
            return
        # TODO: Should we update all metrics consumers here ?

    def _update_new_metrics_consumer(self, event):
        """Set Prometheus scrape configuration for all targets."""
        if not self.unit.is_leader():
            return

        if not self._has_metrics_providers():
            self.unit.status = BlockedStatus("missing metrics provider")
            return

        self.unit.status = MaintenanceStatus(
            "Forwarding scrape jobs and alert rules for new metrics consumers"
        )

        self._update_metrics_consumer_relations([event.relation])

        self.unit.status = ActiveStatus()

    def _update_all_metrics_consumers(self, _):
        """Update all scrape configuration jobs for all metrics consumers."""
        if not self.unit.is_leader():
            return

        if not self._has_metrics_consumers():
            self.unit.status = BlockedStatus("missing metrics consumer")
            return

        self.unit.status = MaintenanceStatus(
            "Updating scrape jobs and alert rules for all metrics consumer"
        )

        self._update_metrics_consumer_relations(self.model.relations[self._metrics_consumer_relation_name])

        self.unit.status = ActiveStatus()

    def _update_metrics_consumer_relations(self, metrics_consumer_relations):
        if not metrics_consumer_relations:
            logger.debug("empty list of metrics consumer relations")
            return

        prometheus_configurations = self._prometheus_configurations

        scrape_jobs = json.dumps(prometheus_configurations["scrape_jobs"])
        alert_rules = json.dumps(prometheus_configurations["alert_rules"])

        for consumer_relation in metrics_consumer_relations:
            consumer_relation.data[self.app]["scrape_jobs"] = scrape_jobs
            consumer_relation.data[self.app]["alert_rules"] = alert_rules
            logger.debug("Updated metrics consumer %s", consumer_relation.app)

    @property
    def _prometheus_configurations(self):
        config = self.model.config.items()

        configured_jobs = []
        for job in self._metrics_providers.jobs():
            job.update(config)
            configured_jobs.append(job)

        alerts = self._metrics_providers.alerts()

        return {"scrape_jobs": configured_jobs, "alert_rules": alerts}


if __name__ == "__main__":
    main(PrometheusScrapeConfigCharm)
