# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import json
import typing
import unittest

from charms.observability_libs.v0.juju_topology import JujuTopology
from ops.model import ActiveStatus, BlockedStatus, WaitingStatus
from ops.testing import Harness

from charm import PrometheusScrapeConfigCharm


class TestCharm(unittest.TestCase):
    @classmethod
    def _scrape_metadata(cls, app_name: str):
        """Scrape metadata for prometheus_scrape."""
        return json.dumps(
            JujuTopology(
                model="model",
                model_uuid="f2c1b2a6-e006-11eb-ba80-0242ac130004",
                application=app_name,
                unit="cassandra-k8s/0",
                charm_name="cassandra-k8s",
            ).as_dict()
        )

    @classmethod
    def _unit_data(cls, app_name: str):
        """Unit data for prometheus_scrape to translate star notation ("*:8000") correctly."""
        return {
            "prometheus_scrape_unit_address": "whatever.cluster.local",
            "prometheus_scrape_unit_name": f"{app_name}/0",
        }

    def setUp(self):
        """Flake8 forces me to write meaningless docstrings."""
        self.harness = Harness(PrometheusScrapeConfigCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin_with_initial_hooks()
        self.harness.update_config({"scrape_interval": "1s"})

    def test_change_scrape_interval(self):
        """Ensure one downstream is updated correctly."""
        self.harness.set_leader(True)

        upstream_rel_id = self.harness.add_relation("configurable-scrape-jobs", "cassandra-k8s")
        self.harness.add_relation_unit(upstream_rel_id, "cassandra-k8s/0")
        self.harness.update_relation_data(
            upstream_rel_id,
            "cassandra-k8s",
            {
                "scrape_jobs": json.dumps(
                    [{"metrics_path": "/metrics", "static_configs": [{"targets": ["*:9500"]}]}]
                ),
                "scrape_metadata": self._scrape_metadata("cassandra-k8s-1"),
            },
        )
        self.harness.update_relation_data(
            upstream_rel_id, "cassandra-k8s/0", self._unit_data("cassandra-k8s")
        )

        downstream_rel_id = self.harness.add_relation("metrics-endpoint", "prometheus-k8s")
        # Check that is does not really matter whether we have units
        # on Prometheus side

        self.assertEqual(self.harness.model.unit.status, ActiveStatus())

        app_data = self.harness.get_relation_data(downstream_rel_id, self.harness.model.app.name)
        scrape_jobs = typing.cast(str, app_data["scrape_jobs"])
        scrape_jobs = json.loads(scrape_jobs)

        # From scrape-config's config option
        self.assertEqual(scrape_jobs[0]["scrape_interval"], "1s")

        # From upstream charm's app data
        self.assertEqual(scrape_jobs[0]["metrics_path"], "/metrics")

        # From upstream charm's app data (:9500) and unit data (whatever.cluster.local)
        self.assertEqual(
            scrape_jobs[0]["static_configs"][0]["targets"], ["whatever.cluster.local:9500"]
        )

    def test_change_scrape_interval_multiple_downstreams(self):
        """Ensure multiple downstreams are updated correctly."""
        self.harness.set_leader(True)

        upstream_rel_id = self.harness.add_relation("configurable-scrape-jobs", "cassandra-k8s")
        self.harness.add_relation_unit(upstream_rel_id, "cassandra-k8s/0")
        self.harness.update_relation_data(
            upstream_rel_id,
            "cassandra-k8s",
            {
                "scrape_jobs": json.dumps(
                    [{"metrics_path": "/metrics", "static_configs": [{"targets": ["*:9500"]}]}]
                ),
                "scrape_metadata": self._scrape_metadata("cassandra-k8s-1"),
            },
        )
        self.harness.update_relation_data(
            upstream_rel_id, "cassandra-k8s/0", self._unit_data("cassandra-k8s")
        )

        downstream1_rel_id = self.harness.add_relation("metrics-endpoint", "prometheus-k8s-1")
        downstream2_rel_id = self.harness.add_relation("metrics-endpoint", "prometheus-k8s-2")
        # It does not really matter whether we have units on Prometheus side

        self.assertEqual(self.harness.model.unit.status, ActiveStatus())

        for rel_id in [downstream1_rel_id, downstream2_rel_id]:
            with self.subTest(rel_id=rel_id):
                app_data = self.harness.get_relation_data(
                    downstream1_rel_id, self.harness.model.app.name
                )
                scrape_jobs = typing.cast(str, app_data["scrape_jobs"])
                scrape_jobs = json.loads(scrape_jobs)

                # From scrape-config's config option
                self.assertEqual(scrape_jobs[0]["scrape_interval"], "1s")

                # From upstream charm's app data
                self.assertEqual(scrape_jobs[0]["metrics_path"], "/metrics")

                # From upstream charm's app data (:9500) and unit data (whatever.cluster.local)
                self.assertEqual(
                    scrape_jobs[0]["static_configs"][0]["targets"], ["whatever.cluster.local:9500"]
                )

    def test_change_scrape_interval_multiple_upstreams(self):
        """Ensure multiple upstream jobs are passed on correctly."""
        self.harness.set_leader(True)

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
                ),
                "scrape_metadata": self._scrape_metadata("cassandra-k8s-1"),
            },
        )
        self.harness.update_relation_data(
            upstream_rel_id, "cassandra-k8s-1/0", self._unit_data("cassandra-k8s-1")
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
                ),
                "scrape_metadata": self._scrape_metadata("cassandra-k8s-2"),
            },
        )
        self.harness.update_relation_data(
            upstream_rel_id, "cassandra-k8s-2/0", self._unit_data("cassandra-k8s-2")
        )

        downstream1_rel_id = self.harness.add_relation("metrics-endpoint", "prometheus-k8s-1")
        self.harness.add_relation_unit(downstream1_rel_id, "prometheus-k8s-2/0")

        downstream2_rel_id = self.harness.add_relation("metrics-endpoint", "prometheus-k8s-2")
        self.harness.add_relation_unit(downstream2_rel_id, "prometheus-k8s-2/1")

        self.assertEqual(self.harness.model.unit.status, ActiveStatus())

        for rel_id in [downstream1_rel_id, downstream2_rel_id]:
            with self.subTest(rel_id=rel_id):
                app_data = self.harness.get_relation_data(
                    downstream1_rel_id, self.harness.model.app.name
                )
                scrape_jobs = typing.cast(str, app_data["scrape_jobs"])
                scrape_jobs = json.loads(scrape_jobs)

                # From scrape-config's config option
                self.assertEqual(scrape_jobs[0]["scrape_interval"], "1s")
                self.assertEqual(scrape_jobs[1]["scrape_interval"], "1s")

                # From upstream charm's app data
                self.assertEqual(scrape_jobs[0]["metrics_path"], "/metrics")
                self.assertEqual(scrape_jobs[1]["metrics_path"], "/metrics2")

                # From upstream charm's app data (ports) and unit data (hosts)
                self.assertEqual(
                    scrape_jobs[0]["static_configs"][0]["targets"], ["whatever.cluster.local:9500"]
                )
                self.assertEqual(
                    scrape_jobs[1]["static_configs"][0]["targets"], ["whatever.cluster.local:9600"]
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
            BlockedStatus("missing metrics consumer (relate to prometheus?)"),
        )

    def test_no_upstreams(self):
        """Ensure charm blocks when no upstreams."""
        self.harness.set_leader(True)

        upstream_rel_id = self.harness.add_relation("metrics-endpoint", "prometheus-k8s")
        self.harness.add_relation_unit(upstream_rel_id, "prometheus-k8s/0")

        self.assertEqual(
            self.harness.model.unit.status,
            BlockedStatus("missing metrics provider (relate to upstream charm?)"),
        )

    def test_unused_unit_sets_waiting_status_by_default(self):
        """Ensure that an inactive unit sets waiting status by default."""
        self.harness.set_leader(False)

        self.assertEqual(
            self.harness.model.unit.status,
            WaitingStatus("inactive unit"),
        )

    def test_unused_unit_sets_waiting_status_on_provider_joined(self):
        """Ensure that an inactive unit sets waiting status on provider joined ."""
        self.harness.set_leader(False)

        upstream_rel_id = self.harness.add_relation("configurable-scrape-jobs", "cassandra-k8s")
        self.harness.add_relation_unit(upstream_rel_id, "cassandra-k8s/0")

        self.assertEqual(
            self.harness.model.unit.status,
            WaitingStatus("inactive unit"),
        )

    def test_unused_unit_sets_waiting_status_on_consumer_joined(self):
        """Ensure that an inactive unit sets waiting status on consumer joined."""
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
                "scrape_metadata": self._scrape_metadata("cassandra-k8s"),
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
                "scrape_metadata": json.dumps(
                    {
                        "model": "model",
                        "model_uuid": "f2c1b2a6-e006-11eb-ba80-0242ac130004",
                        "application": "cassandra-k8s",
                        "unit": "cassandra/0",
                        "charm_name": "cassandra-k8s",
                    }
                ),
            },
        )
        app_name = self.harness.model.app.name
        prom_rules = json.loads(
            str(self.harness.get_relation_data(prom_rel_id, app_name).get("alert_rules"))
        )
        self.assertDictEqual(prom_rules, alert_rules)
