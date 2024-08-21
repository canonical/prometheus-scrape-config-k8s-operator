# Prometheus Scrape Config Operator

[![CharmHub Badge](https://charmhub.io/prometheus-scrape-config-k8s/badge.svg)](https://charmhub.io/prometheus-scrape-config-k8s)
[![Release](https://github.com/canonical/prometheus-scrape-config-k8s-operator/actions/workflows/release.yaml/badge.svg)](https://github.com/canonical/prometheus-scrape-config-k8s-operator/actions/workflows/release.yaml)
[![Discourse Status](https://img.shields.io/discourse/status?server=https%3A%2F%2Fdiscourse.charmhub.io&style=flat&label=CharmHub%20Discourse)](https://discourse.charmhub.io)

## Description

The Prometheus scrape config operator is an adapter charm that enables you to
apply a set of configurations to the scrape jobs provided by its upstream
charms, and forward the modified scrape jobs downstream to one or more
consumers that will actually perform the scraping. For a detailed explanation of
the deployment scenario, see [the integration doc](INTEGRATING.md).

## Usage

First, deploy the prometheus and the charm you want to be monitored with a modified configuration.

```sh
$ juju deploy prometheus-k8s prometheus
$ juju deploy your-charm
```

Then, deploy the `prometheus-scrape-configuration` charm, specifying a 
custom scrape interval valid only for the scrape job forwarded to `prometheus-k8s`
through its relation with this charm.

```sh
$ juju deploy \
    prometheus-scrape-config-k8s \
    scrape-interval-config \
    --config scrape_interval=20s
```

Relate the charms together.

```sh
$ juju relate your-charm scrape-interval-config
$ juju relate scrape-interval-config:metrics-endpoint prometheus
```

### `blocked` state

If you relate `prometheus-scrape-config-k8s` only to `prometheus`,
the charm will be in `blocked` state until any other charm relates to it.
This is expected and doesn't mean the environment is in a wrong state.

```
Unit                             Workload  Agent      Address       Ports          Message
prometheus-scrape-config-k8s/0*  blocked   idle                                    missing metrics provider (relate to upstream charm?)
prometheus/0*                    active    idle
your-charm/0*                    active    idle
```

After a `prometheus_scrape` relation is added, the charm will go
into `active` state.

```
$ juju relate your-charm:metrics-endpoint prometheus-scrape-config-k8s:configurable-scrape-jobs
$ juju status
(...)

Unit                             Workload  Agent  Address       Ports          Message
prometheus-scrape-config-k8s/0*  active    idle
prometheus/0*                    active    idle
your-charm/0*                    active    idle
```

## Relations

- A `configurable-scrape-jobs` relation with any Charm that uses the
  `MetricsEndpointProvider` to implement the `prometheus_scrape` interface.
- A `metrics-endpoint` relation with one or more Charms that implement the
  `MetricsEndpointConsumer`, such as the [Prometheus](https://charmhub.io/prometheus-k8s) charm.

## OCI Image

This charm is workloadless, in the sense that it does not use any OCI images to 
spawn additional workloads.

## Contributing

Please see the [Juju SDK docs](https://juju.is/docs/sdk) as well as
[`CONTRIBUTING.md`](CONTRIBUTING.md) for more information on how to
contribute to this charm.
