# Prometheus Scrape Config Operator

The Prometheus scrape config operator enables you to apply a set of configurations
to the scrape jobs provided by its upstream charms, and forward the modified scrape
jobs downstream to one or more consumers that will actually perform the scraping.

## Usage Example

```sh
$ juju deploy prometheus-k8s      # Deploys Prometheus
$ juju deploy cassandra-k8s       # Deploys Cassandra

# Deploys the prometheus-scrape-configuration, specifying a custom scrape interval valid only for the
# scrape job forwarded to prometheus-k8s through its relation with this charm
$ juju deploy prometheus-scrape-configuration scrape-interval-config --config scrape-interval=20s  

# Link cassandra as scrape target, so that Cassandra’s address is used as a
# static_configs in the scrape job
$ juju relate cassandra-k8s scrape-interval-config  
$ juju relate scrape-interval-config prometheus-k8s  
```

## Relations

- A `configurable-scrape-jobs` relation with any Charm that uses the
  `MetricsEndpointProvider` to implement the `prometheus_scrape` interface.
- A `metrics-endpoint` relation with one or more Charms that implement the
  `MetricsEndpointConsumer`, such as the [Prometheus](https://charmhub.io/prometheus-k8s) charm.

## OCI Images

This charm does not need an actual workload: it simply adjusts and forwards relation data.
However, [Juju does need at least one workload container](https://bugs.launchpad.net/juju/+bug/1928991),
which is why this charm declares an effectively unused container with a base Ubuntu LTS 20.04 image.

## Contributing

Please see the [Juju SDK docs](https://juju.is/docs/sdk) for guidelines 
on enhancements to this charm following best practice guidelines, and
`CONTRIBUTING.md` for developer guidance.
