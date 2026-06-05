# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Shared fixtures for the scenario-based unit tests."""

import json

import pytest
from ops import testing

from charm import PrometheusScrapeConfigCharm


@pytest.fixture
def context():
    """A fresh scenario Context for the charm, loading metadata from charmcraft.yaml."""
    return testing.Context(PrometheusScrapeConfigCharm, charm_root=".")


@pytest.fixture
def metrics_provider_relation():
    """A configurable-scrape-jobs relation to an upstream metrics provider with one job."""
    return testing.Relation(
        endpoint="configurable-scrape-jobs",
        interface="prometheus_scrape",
        remote_app_name="cassandra-k8s",
        remote_app_data={
            "scrape_jobs": json.dumps(
                [{"metrics_path": "/metrics", "static_configs": [{"targets": ["*:9500"]}]}]
            ),
            "scrape_metadata": json.dumps(
                {
                    "model": "model",
                    "model_uuid": "20ce8299-3634-4bef-8bd8-5ace6c8816b4",
                    "application": "cassandra-k8s",
                    "unit": "cassandra-k8s/0",
                    "charm_name": "cassandra-k8s",
                }
            ),
        },
        remote_units_data={
            0: {
                "prometheus_scrape_unit_address": "whatever.cluster.local",
                "prometheus_scrape_unit_name": "cassandra-k8s/0",
            }
        },
    )


@pytest.fixture
def metrics_consumer_relation():
    """A metrics-endpoint relation to a downstream consumer such as Prometheus."""
    return testing.Relation(
        endpoint="metrics-endpoint",
        interface="prometheus_scrape",
        remote_app_name="prometheus",
    )


@pytest.fixture
def charm_tracing_relation():
    """A charm-tracing relation pointing at a Tempo coordinator over HTTP."""
    return testing.Relation(
        endpoint="charm-tracing",
        interface="tracing",
        remote_app_name="tempo",
        remote_app_data={
            "receivers": json.dumps(
                [{"protocol": {"name": "otlp_http", "type": "http"}, "url": "http://tempo:4318"}]
            ),
        },
        remote_units_data={0: {}},
    )


@pytest.fixture
def tls_charm_tracing_relation():
    """A charm-tracing relation pointing at a Tempo coordinator over HTTPS."""
    return testing.Relation(
        endpoint="charm-tracing",
        interface="tracing",
        remote_app_name="tempo",
        remote_app_data={
            "receivers": json.dumps(
                [{"protocol": {"name": "otlp_http", "type": "http"}, "url": "https://tempo:4318"}]
            ),
        },
        remote_units_data={0: {}},
    )


@pytest.fixture
def ca_cert_relation():
    """A receive-ca-cert relation supplying a CA used to validate TLS to the tracing backend."""
    return testing.Relation(
        endpoint="receive-ca-cert",
        interface="certificate_transfer",
        remote_app_name="self-signed-certificates",
        remote_app_data={
            "ca": "-----BEGIN CERTIFICATE-----\nMIIBfake\n-----END CERTIFICATE-----",
        },
        remote_units_data={0: {}},
    )
