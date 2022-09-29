# Prometheus Scrape Config Operator

## Description

The Prometheus scrape config operator is an adapter charm that enables you to
apply a set of configurations to the scrape jobs provided by its upstream
charms, and forward the modified scrape jobs downstream to one or more
consumers that will actually perform the scraping. For a detailed explanation of
the deployment scenario, see [the integration doc](INTEGRATING.md).

## Usage

First, deploy the prometheus and the cassandra charms.

```sh
$ juju deploy prometheus-k8s
$ juju deploy cassandra-k8s
```

Then, deploy the `prometheus-scrape-configuration` charm, specifying a 
custom scrape interval valid only for the scrape job forwarded to `prometheus-k8s`
through its relation with this charm.

```sh
$ juju deploy \
    prometheus-scrape-configuration-k8s \
    scrape-interval-config \
    --config scrape_interval=20s
```

Relate the charms together.

```sh
$ juju relate cassandra-k8s scrape-interval-config
$ juju relate scrape-interval-config prometheus-k8s
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
