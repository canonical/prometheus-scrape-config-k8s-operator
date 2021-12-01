# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import json
import unittest

from ops.model import ActiveStatus, BlockedStatus
from ops.testing import Harness

from charm import PrometheusScrapeConfigCharm


class TestCharm(unittest.TestCase):
    def setUp(self):
        """Flake8 forces me to write meaningless docstrings."""
        self.harness = Harness(PrometheusScrapeConfigCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

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

        self.assertEqual(
            json.loads(
                self.harness.get_relation_data(downstream_rel_id, self.harness.model.app.name).get(
                    "scrape_jobs"
                )
            ),
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

        self.assertEqual(
            json.loads(
                self.harness.get_relation_data(
                    downstream1_rel_id, self.harness.model.app.name
                ).get("scrape_jobs")
            ),
            expected_scrape_jobs,
        )
        self.assertEqual(
            json.loads(
                self.harness.get_relation_data(
                    downstream2_rel_id, self.harness.model.app.name
                ).get("scrape_jobs")
            ),
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
        downstream2_rel_id = self.harness.add_relation("metrics-endpoint", "prometheus-k8s-2")
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

        self.assertEqual(
            json.loads(
                self.harness.get_relation_data(
                    downstream1_rel_id, self.harness.model.app.name
                ).get("scrape_jobs")
            ),
            expected_scrape_jobs,
        )
        self.assertEqual(
            json.loads(
                self.harness.get_relation_data(
                    downstream2_rel_id, self.harness.model.app.name
                ).get("scrape_jobs")
            ),
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
                "scrape_jobs": [
                    {"metrics_path": "/metrics", "static_configs": [{"targets": ["*:9500"]}]}
                ]
            },
        )

        self.assertEqual(
            self.harness.model.unit.status,
            BlockedStatus("downstream relations missing"),
        )

    def test_no_upstreams(self):
        """Ensure charm blocks when no upstreams."""
        self.harness.set_leader(True)

        upstream_rel_id = self.harness.add_relation("metrics-endpoint", "prometheus-k8s")
        self.harness.add_relation_unit(upstream_rel_id, "prometheus-k8s/0")

        self.assertEqual(
            self.harness.model.unit.status,
            BlockedStatus("upstream relations missing"),
        )
