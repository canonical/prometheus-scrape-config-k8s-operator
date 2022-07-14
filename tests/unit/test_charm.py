# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import json
import typing
import unittest

from ops.model import ActiveStatus, BlockedStatus, WaitingStatus
from ops.testing import Harness

from charm import PrometheusScrapeConfigCharm


class TestCharm(unittest.TestCase):
    def setUp(self):
        """Flake8 forces me to write meaningless docstrings."""
        self.harness = Harness(PrometheusScrapeConfigCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin_with_initial_hooks()

    def test_change_scrape_interval(self):
        """Ensure one downstream is updated correctly."""
        self.harness.set_leader(True)

        self.harness.update_config({"scrape_interval": "1s"})

        upstream_rel_id = self.harness.add_relation("configurable-scrape-jobs", "cassandra-k8s")
        self.harness.add_relation_unit(upstream_rel_id, "cassandra-k8s/0")
        self.harness.update_relation_data(
            upstream_rel_id,
            "cassandra-k8s",
            {
                "scrape_jobs": json.dumps(
                    [{"metrics_path": "/metrics", "static_configs": [{"targets": ["*:9500"]}]}]
                )
            },
        )

        downstream_rel_id = self.harness.add_relation("metrics-endpoint", "prometheus-k8s")
        # Check that is does not really matter whether we have units
        # on Prometheus side

        self.assertEqual(
            self.harness.model.unit.status,
            ActiveStatus(),
        )

        scrape_jobs = typing.cast(
            str,
            self.harness.get_relation_data(downstream_rel_id, self.harness.model.app.name).get(
                "scrape_jobs"
            ),
        )
        self.assertEqual(
            json.loads(scrape_jobs),
            [
                {
                    "metrics_path": "/metrics",
                    "scrape_interval": "1s",
                    "static_configs": [{"targets": ["*:9500"]}],
                }
            ],
        )

    def test_change_scrape_interval_multiple_downstreams(self):
        """Ensure multiple downstreams are updated correctly."""
        self.harness.set_leader(True)

        self.harness.update_config({"scrape_interval": "1s"})

        upstream_rel_id = self.harness.add_relation("configurable-scrape-jobs", "cassandra-k8s")
        self.harness.add_relation_unit(upstream_rel_id, "cassandra-k8s/0")
        self.harness.update_relation_data(
            upstream_rel_id,
            "cassandra-k8s",
            {
                "scrape_jobs": json.dumps(
                    [
                        {
                            "metrics_path": "/metrics",
                            "static_configs": [{"targets": ["*:9500"]}],
                        }
                    ]
                )
            },
        )

        downstream1_rel_id = self.harness.add_relation("metrics-endpoint", "prometheus-k8s-1")
        downstream2_rel_id = self.harness.add_relation("metrics-endpoint", "prometheus-k8s-2")
        # Check that is does not really matter whether we have units
        # on Prometheus side

        self.assertEqual(self.harness.model.unit.status, ActiveStatus())

        expected_scrape_jobs = [
            {
                "metrics_path": "/metrics",
                "scrape_interval": "1s",
                "static_configs": [{"targets": ["*:9500"]}],
            }
        ]

        scrape_jobs = typing.cast(
            str,
            self.harness.get_relation_data(downstream1_rel_id, self.harness.model.app.name).get(
                "scrape_jobs"
            ),
        )
        self.assertEqual(
            json.loads(scrape_jobs),
            expected_scrape_jobs,
        )

        scrape_jobs = typing.cast(
            str,
            self.harness.get_relation_data(downstream2_rel_id, self.harness.model.app.name).get(
                "scrape_jobs"
            ),
        )
        self.assertEqual(
            json.loads(scrape_jobs),
            expected_scrape_jobs,
        )

    def test_change_scrape_interval_multiple_upstreams(self):
        """Ensure multiple upstream jobs are passed on correctly."""
        self.harness.set_leader(True)

        self.harness.update_config({"scrape_interval": "1s"})

        upstream_rel_id = self.harness.add_relation("configurable-scrape-jobs", "cassandra-k8s-1")
        self.harness.add_relation_unit(upstream_rel_id, "cassandra-k8s-1/0")
        self.harness.update_relation_data(
            upstream_rel_id,
            "cassandra-k8s-1",
            {
                "scrape_jobs": json.dumps(
                    [
                        {
                            "metrics_path": "/metrics",
                            "static_configs": [{"targets": ["*:9500"]}],
                        }
                    ]
                )
            },
        )

        upstream_rel_id = self.harness.add_relation("configurable-scrape-jobs", "cassandra-k8s-2")
        self.harness.add_relation_unit(upstream_rel_id, "cassandra-k8s-2/0")
        self.harness.update_relation_data(
            upstream_rel_id,
            "cassandra-k8s-2",
            {
                "scrape_jobs": json.dumps(
                    [
                        {
                            "metrics_path": "/metrics2",
                            "static_configs": [{"targets": ["*:9600"]}],
                        }
                    ]
                )
            },
        )

        downstream1_rel_id = self.harness.add_relation("metrics-endpoint", "prometheus-k8s-1")
        self.harness.add_relation_unit(downstream1_rel_id, "prometheus-k8s-2/0")

        downstream2_rel_id = self.harness.add_relation("metrics-endpoint", "prometheus-k8s-2")
        self.harness.add_relation_unit(downstream2_rel_id, "prometheus-k8s-2/1")

        # Check that is does not really matter whether we have units
        # on Prometheus side

        self.assertEqual(self.harness.model.unit.status, ActiveStatus())

        expected_scrape_jobs = [
            {
                "metrics_path": "/metrics",
                "scrape_interval": "1s",
                "static_configs": [{"targets": ["*:9500"]}],
            },
            {
                "metrics_path": "/metrics2",
                "scrape_interval": "1s",
                "static_configs": [{"targets": ["*:9600"]}],
            },
        ]

        scrape_jobs = typing.cast(
            str,
            self.harness.get_relation_data(downstream1_rel_id, self.harness.model.app.name).get(
                "scrape_jobs"
            ),
        )
        self.assertEqual(
            json.loads(scrape_jobs),
            expected_scrape_jobs,
        )

        scrape_jobs = typing.cast(
            str,
            self.harness.get_relation_data(downstream2_rel_id, self.harness.model.app.name).get(
                "scrape_jobs"
            ),
        )
        self.assertEqual(
            json.loads(scrape_jobs),
            expected_scrape_jobs,
        )

    def test_no_downstreams(self):
        """Ensure charm blocks when no downstreams."""
        self.harness.set_leader(True)

        upstream_rel_id = self.harness.add_relation("configurable-scrape-jobs", "cassandra-k8s")
        self.harness.add_relation_unit(upstream_rel_id, "cassandra-k8s/0")
        self.harness.update_relation_data(
            upstream_rel_id,
            "cassandra-k8s",
            {
                "scrape_jobs": json.dumps(
                    [{"metrics_path": "/metrics", "static_configs": [{"targets": ["*:9500"]}]}]
                )
            },
        )

        self.assertEqual(
            self.harness.model.unit.status,
            BlockedStatus("missing metrics consumer"),
        )

    def test_no_upstreams(self):
        """Ensure charm blocks when no upstreams."""
        self.harness.set_leader(True)

        upstream_rel_id = self.harness.add_relation("metrics-endpoint", "prometheus-k8s")
        self.harness.add_relation_unit(upstream_rel_id, "prometheus-k8s/0")

        self.assertEqual(
            self.harness.model.unit.status,
            BlockedStatus("missing metrics provider"),
        )

    def test_unused_unit_sets_waiting_status_by_default(self):
        """Ensure that a inactive unit sets waiting status by default."""
        self.harness.set_leader(False)

        self.assertEqual(
            self.harness.model.unit.status,
            WaitingStatus("inactive unit"),
        )

    def test_unused_unit_sets_waiting_status_on_provider_joined(self):
        """Ensure that a inactive unit sets waiting status on provider joined ."""
        self.harness.set_leader(False)

        upstream_rel_id = self.harness.add_relation("configurable-scrape-jobs", "cassandra-k8s")
        self.harness.add_relation_unit(upstream_rel_id, "cassandra-k8s/0")

        self.assertEqual(
            self.harness.model.unit.status,
            WaitingStatus("inactive unit"),
        )

    def test_unused_unit_sets_waiting_status_on_consumer_joined(self):
        """Ensure that a inactive unit sets waiting status on consumer joined."""
        self.harness.set_leader(False)

        upstream_rel_id = self.harness.add_relation("metrics-endpoint", "prometheus-k8s")
        self.harness.add_relation_unit(upstream_rel_id, "prometheus-k8s/0")

        self.assertEqual(
            self.harness.model.unit.status,
            WaitingStatus("inactive unit"),
        )

    def test_alert_rules(self):
        self.harness.set_leader(True)
        prom_rel_id = self.harness.add_relation("metrics-endpoint", "prometheus-k8s")
        workload_rel_id = self.harness.add_relation("configurable-scrape-jobs", "cassandra-k8s")
        self.harness.add_relation_unit(workload_rel_id, "cassandra-k8s/0")
        alert_rules = {
            "groups": [
                {
                    "name": "test_alert",
                    "rules": [
                        {
                            "alert": "alert",
                            "labels": {
                                "juju_model": "test_model",
                                "juju_model_uuid": "test_uuid",
                                "juju_application": "test_app",
                                "juju_charm": "test_charm",
                            },
                        }
                    ],
                }
            ]
        }

        # Set relation data on the "requires" side
        self.harness.update_relation_data(
            workload_rel_id,
            "cassandra-k8s",
            {
                "scrape_jobs": json.dumps(
                    [{"metrics_path": "/metrics", "static_configs": [{"targets": ["*:9500"]}]}]
                ),
                "alert_rules": json.dumps(alert_rules),
            },
        )

        # Verify relation data on the "provides" side matches the "requires" side
        app_name = self.harness.model.app.name
        prom_rules = json.loads(
            str(self.harness.get_relation_data(prom_rel_id, app_name).get("alert_rules"))
        )
        self.assertDictEqual(prom_rules, alert_rules)

    def test_alert_rules_no_rules(self):
        self.harness.set_leader(True)
        prom_rel_id = self.harness.add_relation("metrics-endpoint", "prometheus-k8s")
        workload_rel_id = self.harness.add_relation("configurable-scrape-jobs", "cassandra-k8s")
        self.harness.add_relation_unit(workload_rel_id, "cassandra-k8s/0")
        alert_rules: dict = {}
        self.harness.update_relation_data(
            workload_rel_id,
            "cassandra-k8s",
            {
                "scrape_jobs": json.dumps(
                    [{"metrics_path": "/metrics", "static_configs": [{"targets": ["*:9500"]}]}]
                ),
                "alert_rules": json.dumps(alert_rules),
            },
        )
        app_name = self.harness.model.app.name
        prom_rules = json.loads(
            str(self.harness.get_relation_data(prom_rel_id, app_name).get("alert_rules"))
        )
        self.assertDictEqual(prom_rules, alert_rules)
